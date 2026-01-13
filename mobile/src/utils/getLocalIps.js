// getLocalIP.js
//TODO:Hacer que la ip del backend cambie dependiendo del ambiente
//TODO: Dejar de leakear mi IP y no leakear ñla ip del backend
import os from 'node:os';

function getLocalIP() {
  const nets = os.networkInterfaces();

  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      // IPv4 y no interna (127.0.0.1)
      if (net.family === 'IPv4' && !net.internal) {
        return net.address;
      }
    }
  }

  return '127.0.0.1';
}

module.exports = { getLocalIP };
