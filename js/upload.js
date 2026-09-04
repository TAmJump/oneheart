/* ONE HEART — portrait capture and upload.
   Takes an ID-photo style shot (3:4) with an on-screen guide, or accepts a file.
   Resizes in the browser, then posts to /portrait. */
(function (w, d) {
  "use strict";

  var NAME_MAX = 24;      /* characters allowed on the reverse side */
  var NAME_OK = /^[\p{L}\p{M}\p{N} .,'\u2019\-&\u00B7]+$/u;

  var MIN = 800;          /* shortest side a chosen file must have */
  var MAX = 1600;         /* longest side we keep from a file */
  var SHOT_W = 1200;      /* captured photo, 3:4 like an ID photo */
  var SHOT_H = 1600;
  var QUALITY = 0.88;

  var GUIDE =
    '<svg viewBox="0 0 300 400" preserveAspectRatio="none" aria-hidden="true">' +
    '<ellipse cx="150" cy="168" rx="70" ry="92" fill="none" stroke="rgba(255,255,255,.9)" stroke-width="2" stroke-dasharray="7 6"/>' +
    '<path d="M60 400 C 60 320, 105 286, 150 286 C 195 286, 240 320, 240 400" fill="none" stroke="rgba(255,255,255,.55)" stroke-width="2"/>' +
    '<line x1="150" y1="52" x2="150" y2="70" stroke="rgba(255,255,255,.55)" stroke-width="2"/>' +
    '</svg>';

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

  /* cfg: { endpoint, ids:{cam,file,stage,send,msg}, order: function -> {orderId,email} } */
  w.portraitUpload = function (cfg) {
    var ids = cfg.ids;
    var file = el(ids.file), stage = el(ids.stage), send = el(ids.send), msg = el(ids.msg);
    var cam = ids.cam ? el(ids.cam) : null;
    var nameBox = ids.name ? el(ids.name) : null;
    var count = ids.count ? el(ids.count) : null;
    var data = null, busy = false, done = false, stream = null, video = null;

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
      ready(false);
    }

    function preview(src, again) {
      stop();
      stage.innerHTML =
        '<div class="shot"><img src="' + src + '" alt=""></div>' +
        (again ? '<button class="btn alt" type="button" id="' + ids.stage + '-retake">Take another</button>' : "");
      data = src;
      ready(true);
      if (again) {
        el(ids.stage + "-retake").addEventListener("click", function () { openCamera(); });
      }
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
        '<div class="frame"><video playsinline autoplay muted></video>' + GUIDE + '</div>' +
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
        var n = Array.from(niceName()).length;
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

    send.addEventListener("click", function () {
      if (busy || done || !data) { return; }
      var who = cfg.order();
      if (!who) { return; }
      var nm = niceName();
      if (nameBox) {
        if (!nm) { say("Type the name or initials that go on the reverse of your piece."); nameBox.focus(); return; }
        if (Array.from(nm).length > NAME_MAX) { say("That name is longer than " + NAME_MAX + " characters. Shorten it, or use initials."); nameBox.focus(); return; }
        if (!NAME_OK.test(nm)) { say("Letters, numbers, spaces and . , ' - & only. Emoji cannot be engraved on the reverse."); nameBox.focus(); return; }
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
          if (e === "name_chars") { throw new Error("That name uses characters we cannot put on the reverse. Letters, numbers, spaces and . , ' - & only."); }
          throw new Error("The photograph was not received. Please try again, or email it to info@tamjump.com.");
        }
        done = true;
        stop();
        send.textContent = "Sent";
        if (cam) { cam.disabled = true; }
        if (nameBox) { nameBox.disabled = true; }
        say("Your portrait is in. A confirmation is on its way to you, and nothing else is needed.", true);
      }).catch(function (err) {
        busy = false;
        send.disabled = false;
        send.textContent = "Send this photograph";
        say(err.message);
      });
    });
  };
})(window, document);
