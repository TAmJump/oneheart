/* ONE HEART — portrait capture and upload.
   Takes an ID-photo style shot (3:4) with an on-screen guide, or accepts a file.
   Resizes in the browser, then posts to /portrait. */
(function (w, d) {
  "use strict";

  var NAME_MAX = 24;      /* characters allowed on the reverse side */

  /* Any language, and any symbol that types out in black and white (\u2661 \u2605 \u266A).
     Colour emoji are refused: they cannot be engraved on the reverse. */
  function nameLen(s) {
    return Array.from(s).filter(function (c) {
      return c !== "\uFE0E" && c !== "\uFE0F" && !/\p{M}/u.test(c);
    }).length;
  }

  function nameOk(s) {
    if (!s) { return false; }
    var cp = Array.from(s);
    for (var i = 0; i < cp.length; i++) {
      var c = cp[i], next = cp[i + 1];
      if (c === "\uFE0F" || c === "\u200D") { return false; }
      if (c === "\uFE0E") { continue; }
      if (/[\u{1F1E6}-\u{1F1FF}]/u.test(c)) { return false; }
      if (/\p{Emoji_Presentation}/u.test(c) && next !== "\uFE0E") { return false; }
      if (/[\p{L}\p{M}\p{N}\p{S}\p{P} ]/u.test(c)) { continue; }
      return false;
    }
    return true;
  }

  var MIN = 800;          /* shortest side a chosen file must have */
  var MAX = 1600;         /* longest side we keep from a file */
  var SHOT_W = 1200;      /* captured photo, 3:4 like an ID photo */
  var SHOT_H = 1600;
  var QUALITY = 0.88;
  var BG = "#F2F1EE";     /* not pure white, so light clothing still reads */
  var TOP = 0.235;        /* share of the card kept clear for the words */

  /* ID-photo guide. mode "live" darkens everything outside the head area,
     mode "check" is outline only, laid over the shot that was taken. */
  function guide(mode) {
    var live = mode === "live";
    return '<svg class="guide" viewBox="0 0 300 400" aria-hidden="true">' +
      '<defs>' +
        '<filter id="ohb"><feGaussianBlur stdDeviation="9"/></filter>' +
        '<mask id="ohm">' +
          '<rect width="300" height="400" fill="#fff"/>' +
          '<ellipse cx="150" cy="170" rx="78" ry="101" fill="#000" filter="url(#ohb)"/>' +
        '</mask>' +
      '</defs>' +
      (live ? '<rect width="300" height="400" fill="rgba(0,0,0,.58)" mask="url(#ohm)"/>' : '') +
      '<ellipse cx="150" cy="170" rx="70" ry="92" fill="none" stroke="#FFD900" stroke-width="1.6" stroke-dasharray="8 7" opacity="' + (live ? '.95' : '.9') + '"/>' +
      '<path d="M56 400 C 56 322, 103 288, 150 288 C 197 288, 244 322, 244 400" fill="none" stroke="#FFD900" stroke-width="1.4" opacity="' + (live ? '.5' : '.45') + '"/>' +
      '<line x1="150" y1="46" x2="150" y2="62" stroke="#E53935" stroke-width="2.4"/>' +
      '<path d="M14 44 L14 14 L44 14" fill="none" stroke="#FFD900" stroke-width="3"/>' +
      '<path d="M256 14 L286 14 L286 44" fill="none" stroke="#FFD900" stroke-width="3"/>' +
      '<path d="M286 356 L286 386 L256 386" fill="none" stroke="#FFD900" stroke-width="3"/>' +
      '<path d="M44 386 L14 386 L14 356" fill="none" stroke="#FFD900" stroke-width="3"/>' +
      '</svg>';
  }

  function el(id) { return d.getElementById(id); }

  function readFile(file) {
    return new Promise(function (res, rej) {
      var fr = new FileReader();
      fr.onload = function () { res(fr.result); };
      fr.onerror = function () { rej(new Error("That file could not be read.")); };
      fr.readAsDataURL(file);
    });
  }

  function loadImage(src) {
    return new Promise(function (res, rej) {
      var im = new Image();
      im.onload = function () { res(im); };
      im.onerror = function () { rej(new Error("That file is not an image we can read.")); };
      im.src = src;
    });
  }

  /* Background removal. The model is fetched on demand; if anything fails we
     keep the photograph exactly as it was taken. */
  var SEG_BASE = "https://cdn.jsdelivr.net/npm/@mediapipe/selfie_segmentation@0.1.1675465747/";
  var segLoad = null;

  function loadSeg() {
    if (segLoad) { return segLoad; }
    segLoad = new Promise(function (res, rej) {
      var t = d.createElement("script");
      t.src = SEG_BASE + "selfie_segmentation.js";
      t.crossOrigin = "anonymous";
      t.onload = function () { res(w.SelfieSegmentation); };
      t.onerror = function () { rej(new Error("no model")); };
      d.head.appendChild(t);
      setTimeout(function () { rej(new Error("slow model")); }, 20000);
    });
    return segLoad;
  }

  /* where the person sits inside the frame, read off the mask at low resolution */
  function measure(maskSource, W, H) {
    var w = 90, h = 120;
    var cv = d.createElement("canvas");
    cv.width = w; cv.height = h;
    var cx = cv.getContext("2d");
    cx.drawImage(maskSource, 0, 0, w, h);
    var px = cx.getImageData(0, 0, w, h).data;
    var x0 = w, y0 = h, x1 = -1, y1 = -1;
    for (var y = 0; y < h; y++) {
      for (var x = 0; x < w; x++) {
        var i = (y * w + x) * 4;
        if (px[i] > 140 || px[i + 3] > 140 && px[i] > 60) {
          if (x < x0) { x0 = x; }
          if (x > x1) { x1 = x; }
          if (y < y0) { y0 = y; }
          if (y > y1) { y1 = y; }
        }
      }
    }
    if (x1 < 0) { return null; }
    return {
      x: x0 / w * W, y: y0 / h * H,
      w: (x1 - x0 + 1) / w * W, h: (y1 - y0 + 1) / h * H
    };
  }

  function cutout(im) {
    return loadSeg().then(function (Seg) {
      return new Promise(function (res, rej) {
        var seg = new Seg({ locateFile: function (f) { return SEG_BASE + f; } });
        seg.setOptions({ modelSelection: 1 });
        var timer = setTimeout(function () { rej(new Error("slow")); }, 20000);
        seg.onResults(function (out) {
          clearTimeout(timer);
          try {
            var W = im.naturalWidth || im.width, H = im.naturalHeight || im.height;
            var cv = d.createElement("canvas");
            cv.width = W; cv.height = H;
            var cx = cv.getContext("2d");
            cx.drawImage(out.segmentationMask, 0, 0, W, H);
            cx.globalCompositeOperation = "source-in";
            cx.drawImage(out.image, 0, 0, W, H);
            cx.globalCompositeOperation = "destination-over";
            cx.fillStyle = BG;
            cx.fillRect(0, 0, W, H);
            cx.globalCompositeOperation = "source-over";
            res({ src: cv.toDataURL("image/jpeg", QUALITY), box: measure(out.segmentationMask, W, H) });
          } catch (err) { rej(err); }
        });
        seg.send({ image: im }).catch(rej);
      });
    });
  }

  function shrink(im) {
    var w0 = im.naturalWidth, h0 = im.naturalHeight;
    if (Math.min(w0, h0) < MIN) {
      throw new Error("That photograph is " + w0 + "\u00D7" + h0 + ". We need at least " +
        MIN + "\u00D7" + MIN + ", so a photo from your camera rather than a saved profile picture.");
    }
    var s = Math.min(1, MAX / Math.max(w0, h0));
    var cv = d.createElement("canvas");
    cv.width = Math.round(w0 * s);
    cv.height = Math.round(h0 * s);
    var cx = cv.getContext("2d");
    cx.imageSmoothingQuality = "high";
    cx.drawImage(im, 0, 0, cv.width, cv.height);
    return cv.toDataURL("image/jpeg", QUALITY);
  }


  /* ---- the piece: front is the photograph, back is the name ---- */

  var CARD_W = 900, CARD_H = 1200, R = 46;

  function roundRect(cx, x, y, w, h, r) {
    cx.beginPath();
    cx.moveTo(x + r, y);
    cx.arcTo(x + w, y, x + w, y + h, r);
    cx.arcTo(x + w, y + h, x, y + h, r);
    cx.arcTo(x, y + h, x, y, r);
    cx.arcTo(x, y, x + w, y, r);
    cx.closePath();
  }

  function frontCard(im, box) {
    var cv = d.createElement("canvas");
    cv.width = CARD_W; cv.height = CARD_H;
    var cx = cv.getContext("2d");
    cx.fillStyle = BG;
    roundRect(cx, 0, 0, CARD_W, CARD_H, R);
    cx.fill();
    cx.save();
    roundRect(cx, 0, 0, CARD_W, CARD_H, R);
    cx.clip();
    var top = CARD_H * TOP;
    if (box && box.w > 0 && box.h > 0) {
      var s = Math.min((CARD_H - top) / box.h, (CARD_W * 0.96) / box.w);
      var w = box.w * s, h = box.h * s;
      cx.drawImage(im, box.x, box.y, box.w, box.h, (CARD_W - w) / 2, CARD_H - h, w, h);
    } else {
      var f = Math.max(CARD_W / im.naturalWidth, (CARD_H - top) / im.naturalHeight);
      var fw = im.naturalWidth * f, fh = im.naturalHeight * f;
      cx.drawImage(im, (CARD_W - fw) / 2, CARD_H - fh, fw, fh);
    }
    cx.restore();

    var lines = [["WE ARE ALL", "#111111"], ["ONE HEART", "#E53935"]];
    var size = Math.round(top * 0.40);
    cx.textAlign = "center";
    cx.textBaseline = "middle";
    while (size > 20) {
      cx.font = '900 ' + size + 'px Inter, Helvetica, Arial, sans-serif';
      var widest = Math.max(cx.measureText(lines[0][0]).width, cx.measureText(lines[1][0]).width);
      if (widest <= CARD_W * 0.88) { break; }
      size -= 2;
    }
    var y = top * 0.44;
    lines.forEach(function (l) {
      cx.fillStyle = l[1];
      cx.fillText(l[0], CARD_W / 2, y);
      y += size * 1.02;
    });

    cx.strokeStyle = "#111111";
    cx.lineWidth = 6;
    roundRect(cx, 3, 3, CARD_W - 6, CARD_H - 6, R - 3);
    cx.stroke();
    return cv;
  }

  function backCard(name) {
    var cv = d.createElement("canvas");
    cv.width = CARD_W; cv.height = CARD_H;
    var cx = cv.getContext("2d");
    cx.fillStyle = "#0B0B0B";
    roundRect(cx, 0, 0, CARD_W, CARD_H, R);
    cx.fill();
    cx.strokeStyle = "#E0B34A";
    cx.lineWidth = 3;
    roundRect(cx, 26, 26, CARD_W - 52, CARD_H - 52, R - 16);
    cx.stroke();

    var size = 150;
    cx.textAlign = "center";
    cx.textBaseline = "middle";
    cx.fillStyle = "#E9BC57";
    while (size > 28) {
      cx.font = size + 'px "Great Vibes", "Hiragino Mincho ProN", "Yu Mincho", serif';
      if (cx.measureText(name).width <= CARD_W - 200) { break; }
      size -= 4;
    }
    cx.fillText(name, CARD_W / 2, CARD_H / 2);
    return cv;
  }

  function sheet(front, back) {
    var pad = 70, gap = 70;
    var cv = d.createElement("canvas");
    cv.width = pad * 2 + CARD_W * 2 + gap;
    cv.height = pad * 2 + CARD_H + 120;
    var cx = cv.getContext("2d");
    cx.fillStyle = "#FFD900";
    cx.fillRect(0, 0, cv.width, cv.height);
    cx.drawImage(front, pad, pad);
    cx.drawImage(back, pad + CARD_W + gap, pad);
    cx.fillStyle = "#111111";
    cx.textBaseline = "alphabetic";
    cx.textAlign = "center";
    cx.font = '600 46px Inter, Helvetica, Arial, sans-serif';
    cx.fillText("ONE PIECE OF ONE HEART", cv.width / 2, pad + CARD_H + 84);
    return cv;
  }

  function showCard(stage, ids, src, name, box, onSheet) {
    var box = d.createElement("div");
    box.className = "piece";
    stage.innerHTML = "";
    stage.appendChild(box);
    box.innerHTML = '<p class="cap">This is your piece. The front carries your face, the back carries your name. ' +
      'It goes into the artwork exactly like this.</p><div class="cards"></div>' +
      '<button class="btn alt" type="button" id="' + ids.stage + '-save">Save your piece</button>';
    var cards = box.querySelector(".cards");

    loadImage(src).then(function (im) {
      var ready = w.document.fonts && w.document.fonts.load
        ? w.document.fonts.load('60px "Great Vibes"').catch(function () { return null; })
        : Promise.resolve(null);
      return ready.then(function () {
        var f = frontCard(im, box), b = backCard(name);
        if (onSheet) { onSheet(sheet(f, b).toDataURL("image/jpeg", 0.9)); }
        [f, b].forEach(function (c) {
          var i = new Image();
          i.src = c.toDataURL("image/png");
          i.alt = "";
          cards.appendChild(i);
        });
        el(ids.stage + "-save").addEventListener("click", function () {
          var a = d.createElement("a");
          a.href = sheet(f, b).toDataURL("image/png");
          a.download = "one-heart-piece.png";
          a.click();
        });
      });
    }).catch(function () { box.innerHTML = ""; });
  }

  /* cfg: { endpoint, ids:{cam,file,stage,send,msg}, order: function -> {orderId,email} } */
  w.portraitUpload = function (cfg) {
    var ids = cfg.ids;
    var file = el(ids.file), stage = el(ids.stage), send = el(ids.send), msg = el(ids.msg);
    var cam = ids.cam ? el(ids.cam) : null;
    var nameBox = ids.name ? el(ids.name) : null;
    var count = ids.count ? el(ids.count) : null;
    var data = null, busy = false, done = false, stream = null, video = null, box = null;

    function say(text, ok) {
      msg.textContent = text || "";
      msg.style.display = text ? "block" : "none";
      msg.className = "msg" + (ok ? " ok" : "");
    }

    function ready(on) { send.disabled = !on; }

    function stop() {
      if (stream) {
        stream.getTracks().forEach(function (t) { t.stop(); });
        stream = null;
      }
      video = null;
    }

    function clear() {
      stop();
      stage.innerHTML = "";
      data = null;
      box = null;
      ready(false);
    }

    function paint(src, again, plain, cut) {
      stage.innerHTML =
        '<div class="shot">' + '<img src="' + src + '" alt="">' + (again ? guide("check") : "") + '</div>' +
        (again ? '<p class="cap">Is your face inside the outline, with your shoulders in the frame? If not, take another.</p>' : "") +
        '<div class="uprow">' +
        (again ? '<button class="btn alt" type="button" id="' + ids.stage + '-retake">Take another</button>' : "") +
        (cut ? '<button class="link" type="button" id="' + ids.stage + '-swap"></button>' : "") +
        '</div>';
      data = src;
      ready(true);
      if (again) {
        el(ids.stage + "-retake").addEventListener("click", function () { openCamera(); });
      }
      if (cut) {
        var swap = el(ids.stage + "-swap");
        swap.textContent = src === cut ? "Keep my own background" : "Put me on a white background";
        swap.addEventListener("click", function () {
          paint(src === cut ? plain : cut, again, plain, cut);
        });
      }
    }

    function preview(src, again) {
      stop();
      paint(src, again, src, null);
      var busyNote = d.createElement("p");
      busyNote.className = "cap";
      busyNote.textContent = "Taking the background out\u2026";
      stage.appendChild(busyNote);
      loadImage(src).then(cutout).then(function (cut) {
        box = cut.box;
        paint(cut.src, again, src, cut.src);
      }).catch(function () {
        if (busyNote.parentNode) { busyNote.parentNode.removeChild(busyNote); }
      });
    }

    function openCamera() {
      if (done) { return; }
      say("");
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        say("This browser will not open the camera here. Choose a file instead.");
        return;
      }
      clear();
      stage.innerHTML =
        '<div class="frame"><video playsinline autoplay muted></video>' + guide("live") + '</div>' +
        '<p class="cap">Fit your face inside the outline. Head and shoulders, looking at the camera, in even light.</p>' +
        '<button class="btn" type="button" id="' + ids.stage + '-shot">Take the photo</button>';
      video = stage.querySelector("video");

      navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1440 }, height: { ideal: 1920 } },
        audio: false
      }).then(function (s) {
        stream = s;
        video.srcObject = s;
        return video.play();
      }).catch(function () {
        clear();
        say("The camera could not be opened. Allow camera access for this site, or choose a file instead.");
      });

      el(ids.stage + "-shot").addEventListener("click", function () {
        if (!video || !video.videoWidth) { return; }
        var vw = video.videoWidth, vh = video.videoHeight;
        /* the frame shows a 3:4 window cropped from the centre of the stream */
        var scale = Math.max(SHOT_W / vw, SHOT_H / vh);
        var sw = SHOT_W / scale, sh = SHOT_H / scale;
        var cv = d.createElement("canvas");
        cv.width = SHOT_W;
        cv.height = SHOT_H;
        var cx = cv.getContext("2d");
        cx.imageSmoothingQuality = "high";
        cx.drawImage(video, (vw - sw) / 2, (vh - sh) / 2, sw, sh, 0, 0, SHOT_W, SHOT_H);
        preview(cv.toDataURL("image/jpeg", QUALITY), true);
      });
    }

    function niceName() {
      return nameBox ? nameBox.value.trim().replace(/\s+/g, " ") : "";
    }

    if (nameBox && count) {
      var tick = function () {
        var n = nameLen(niceName());
        count.textContent = n + " / " + NAME_MAX;
        count.className = "count" + (n > NAME_MAX ? " over" : "");
      };
      nameBox.addEventListener("input", tick);
      tick();
    }

    if (cam) { cam.addEventListener("click", openCamera); }

    file.addEventListener("change", function () {
      var f = file.files && file.files[0];
      if (!f) { return; }
      clear();
      if (!/^image\/(jpeg|png)$/.test(f.type)) {
        say("Send a JPEG or a PNG.");
        return;
      }
      say("");
      readFile(f).then(loadImage).then(function (im) {
        preview(shrink(im), false);
      }).catch(function (err) {
        say(err.message || "That photograph could not be prepared.");
      });
    });

    if (ids.recall && el(ids.recall) && cfg.pieceEndpoint) {
      var recall = el(ids.recall);
      recall.addEventListener("click", function () {
        var who = cfg.order();
        if (!who) { return; }
        recall.disabled = true;
        recall.textContent = "Looking";
        say("");
        fetch(cfg.pieceEndpoint, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ orderId: who.orderId, email: who.email })
        }).then(function (r) {
          return r.json().then(function (j) { return { ok: r.ok, j: j }; });
        }).then(function (out) {
          recall.disabled = false;
          recall.textContent = "See your piece";
          if (!out.ok) {
            var e = (out.j && out.j.error) || "";
            if (e === "no_portrait") { throw new Error("No photograph has been sent for this order yet."); }
            if (e === "no_order") { throw new Error("We cannot find that order number. Check it against your confirmation email."); }
            if (e === "email_mismatch") { throw new Error("That email address does not match the one on this order."); }
            throw new Error("Your piece could not be loaded. Please try again.");
          }
          stop();
          showCard(stage, ids, out.j.image, out.j.name, null, null);
        }).catch(function (err) {
          recall.disabled = false;
          recall.textContent = "See your piece";
          say(err.message);
        });
      });
    }

    send.addEventListener("click", function () {
      if (busy || done || !data) { return; }
      var who = cfg.order();
      if (!who) { return; }
      var nm = niceName();
      if (nameBox) {
        if (!nm) { say("Type the name or initials that go on the reverse of your piece."); nameBox.focus(); return; }
        if (nameLen(nm) > NAME_MAX) { say("That name is longer than " + NAME_MAX + " characters. Shorten it, or use initials."); nameBox.focus(); return; }
        if (!nameOk(nm)) { say("Colour emoji cannot go on the reverse. Black and white symbols such as \u2661 \u2605 \u266A are fine."); nameBox.focus(); return; }
      }
      busy = true;
      send.disabled = true;
      send.textContent = "Sending";
      say("");
      fetch(cfg.endpoint, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ orderId: who.orderId, email: who.email, image: data, name: nm })
      }).then(function (r) {
        return r.json().then(function (j) { return { ok: r.ok, j: j }; });
      }).then(function (out) {
        if (!out.ok) {
          var e = (out.j && out.j.error) || "";
          if (e === "no_order") { throw new Error("We cannot find that order number. Check it against your confirmation email."); }
          if (e === "email_mismatch") { throw new Error("That email address does not match the one on this order."); }
          if (e === "too_large") { throw new Error("That photograph is too large even after resizing. Try another one."); }
          if (e === "bad_image") { throw new Error("That file could not be read as a photograph."); }
          if (e === "name_long") { throw new Error("That name is longer than " + NAME_MAX + " characters."); }
          if (e === "name_chars") { throw new Error("That name uses characters we cannot put on the reverse. Colour emoji are the usual reason."); }
          throw new Error("The photograph was not received. Please try again, or email it to info@tamjump.com.");
        }
        done = true;
        stop();
        send.textContent = "Sent";
        if (cam) { cam.disabled = true; }
        if (nameBox) { nameBox.disabled = true; }
        say("Your portrait is in. A confirmation is on its way to you, and nothing else is needed.", true);
        showCard(stage, ids, data, nm, box, function (card) {
          fetch(cfg.endpoint, {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ orderId: who.orderId, email: who.email, card: card })
          }).catch(function () {});
        });
      }).catch(function (err) {
        busy = false;
        send.disabled = false;
        send.textContent = "Send this photograph";
        say(err.message);
      });
    });
  };
})(window, document);
