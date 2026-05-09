const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('AIA', {
  runPython: (script, args) => ipcRenderer.invoke('run-python', { script, args }),
  onLog: (callback) => {
    ipcRenderer.on('log', (event, data) => callback(data));
    return () => ipcRenderer.removeAllListeners('log');
  },
  onProgress: (callback) => {
    ipcRenderer.on('progress', (event, percent) => callback(percent));
    return () => ipcRenderer.removeAllListeners('progress');
  },
  selectFile: (options) => ipcRenderer.invoke('select-file', options),
  getPythonVersion: () => ipcRenderer.invoke('get-python-version')
});