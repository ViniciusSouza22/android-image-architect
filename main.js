const { app, BrowserWindow, ipcMain, dialog, nativeImage, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let pythonPath = 'python';
let pythonVersion = '3.x';

function resolvePython() {
  return new Promise((resolve, reject) => {
    const test = spawn(pythonPath, ['--version']);
    test.stdout.on('data', (data) => {
      pythonVersion = data.toString().trim();
    });
    test.on('close', (code) => {
      if (code === 0) {
        resolve(pythonPath);
      } else {
        dialog.showOpenDialog({
          title: 'Selecione o executável do Python (python.exe)',
          filters: [{ name: 'Python', extensions: ['exe'] }],
          properties: ['openFile']
        }).then(result => {
          if (!result.canceled && result.filePaths.length > 0) {
            pythonPath = result.filePaths[0];
            resolve(pythonPath);
          } else {
            reject(new Error('Python não encontrado'));
          }
        });
      }
    });
    test.on('error', () => {
      dialog.showOpenDialog({
        title: 'Selecione o executável do Python (python.exe)',
        filters: [{ name: 'Python', extensions: ['exe'] }],
        properties: ['openFile']
      }).then(result => {
        if (!result.canceled && result.filePaths.length > 0) {
          pythonPath = result.filePaths[0];
          resolve(pythonPath);
        } else {
          reject(new Error('Python não encontrado'));
        }
      });
    });
  });
}

let mainWindow;

function createWindow() {
  // ===== TRATAMENTO DO ÍCONE =====
  let appIcon;
  const possibleIcons = [
    path.join(__dirname, 'assets', 'icon.png'),
    path.join(__dirname, 'assets', 'icon.ico'),
    path.join(process.resourcesPath, 'assets', 'icon.png'),
    path.join(process.resourcesPath, 'assets', 'icon.ico')
  ];

  for (const iconPath of possibleIcons) {
    if (fs.existsSync(iconPath)) {
      appIcon = nativeImage.createFromPath(iconPath);
      appIcon = appIcon.resize({ width: 64, height: 64 });
      break;
    }
  }
  if (!appIcon) appIcon = nativeImage.createEmpty();

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: 'Android Image Architect',
    icon: appIcon,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    backgroundColor: '#080a0c',
    show: false,
    autoHideMenuBar: true,
    menuBarVisible: false
  });

  mainWindow.loadFile('aia-ui.html');
  mainWindow.setMenu(null);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });
}

app.whenReady().then(async () => {
  try {
    pythonPath = await resolvePython();
  } catch (e) {
    console.error('Python não disponível:', e.message);
  }
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// ========== IPC HANDLERS ==========
ipcMain.handle('select-file', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options || { properties: ['openFile'] });
  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

ipcMain.handle('run-python', async (event, { script, args }) => {
  const baseDir = app.isPackaged ? process.resourcesPath : __dirname;
  const pythonScript = path.join(baseDir, 'python', script);
  const toolsDir = path.join(baseDir, 'tools');

  // 📦 Verificação especial para scripts que precisam de 7z
  if (script === 'extract_fs.py') {
    const sevenZipPath = path.join(toolsDir, '7z.exe');
    if (!fs.existsSync(sevenZipPath)) {
      // Mostra diálogo nativo oferecendo download
      const result = await dialog.showMessageBox(mainWindow, {
        type: 'warning',
        title: 'Ferramenta 7-Zip não encontrada',
        message: 'O 7-Zip é necessário para extrair o conteúdo de imagens de sistema (EXT4/EROFS). Deseja baixar o instalador agora?',
        buttons: ['Sim', 'Não'],
        defaultId: 0,
        cancelId: 1
      });

      if (result.response === 0) {
        // Abre o link oficial do 7-Zip no navegador
        shell.openExternal('https://www.7-zip.org/download.html');
      }

      // Retorna um erro informativo (não executa o script)
      return { error: '7-Zip não instalado. Link de download fornecido.' };
    }
  }

  const env = { ...process.env, AIA_TOOLS_DIR: toolsDir, PYTHONIOENCODING: 'utf-8' };

  return new Promise((resolve, reject) => {
    const proc = spawn(pythonPath, [pythonScript, ...args], { env });

    let stdoutData = '';
    let stderrData = '';

    proc.stdout.on('data', (data) => {
      const text = data.toString('utf-8');
      stdoutData += text;
      mainWindow.webContents.send('log', { type: 'stdout', text });
      const match = text.match(/PROGRESS:(\d+)/);
      if (match) {
        mainWindow.webContents.send('progress', parseInt(match[1]));
      }
    });

    proc.stderr.on('data', (data) => {
      const text = data.toString('utf-8');
      stderrData += text;
      mainWindow.webContents.send('log', { type: 'stderr', text });
    });

    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Script ${script} falhou com código ${code}\n${stderrData}`));
        return;
      }
      const lines = stdoutData.trim().split('\n');
      let jsonResult = {};
      const lastLine = lines[lines.length - 1];
      if (lastLine.startsWith('{')) {
        try {
          jsonResult = JSON.parse(lastLine);
        } catch (e) {
          console.warn('Não foi possível parsear JSON do script:', e);
        }
      }
      resolve(jsonResult);
    });

    proc.on('error', (err) => {
      reject(err);
    });
  });
});

ipcMain.handle('get-python-version', () => pythonVersion);