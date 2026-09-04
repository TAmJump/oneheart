/* ONE HEART — portrait upload.
   Resizes the photograph in the browser, then posts it to /portrait.
   Used by /participate/ (order is known) and /portrait/ (order is typed in). */
(function (w, d) {
  "use strict";

  var MIN = 800;        /* shortest side the photograph must have */
  var MAX = 1600;       /* longest side we keep */
  var QUALITY = 0.86;

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
        MIN + "\u00D7" + MIN + " so the face still reads at full resolution.");
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

  /* cfg: { endpoint, ids:{file,prev,send,msg,name}, order: function -> {orderId,email} } */
  w.portraitUpload = function (cfg) {
    var ids = cfg.ids;
    var file = el(ids.file), prev = el(ids.prev), send = el(ids.send), msg = el(ids.msg);
    var name = ids.name ? el(ids.name) : null;
    var data = null, busy = false, done = false;

    function say(text, ok) {
      msg.textContent = text || "";
      msg.style.display = text ? "block" : "none";
      msg.className = "msg" + (ok ? " ok" : "");
    }

    function ready(on) { send.disabled = !on; }

    file.addEventListener("change", function () {
      var f = file.files && file.files[0];
      data = null;
      ready(false);
      prev.innerHTML = "";
      if (name) name.textContent = "";
      if (!f) { return; }
      if (!/^image\/(jpeg|png)$/.test(f.type)) {
        say("Send a JPEG or a PNG.");
        return;
      }
      say("");
      if (name) name.textContent = f.name;
      readFile(f).then(loadImage).then(function (im) {
        data = shrink(im);
        var thumb = new Image();
        thumb.src = data;
        thumb.alt = "";
        prev.appendChild(thumb);
        ready(true);
      }).catch(function (err) {
        say(err.message || "That photograph could not be prepared.");
      });
    });

    send.addEventListener("click", function () {
      if (busy || done || !data) { return; }
      var who = cfg.order();
      if (!who) { return; }
      busy = true;
      send.disabled = true;
      send.textContent = "Sending";
      say("");
      fetch(cfg.endpoint, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ orderId: who.orderId, email: who.email, image: data })
      }).then(function (r) {
        return r.json().then(function (j) { return { ok: r.ok, j: j }; });
      }).then(function (out) {
        if (!out.ok) {
          var e = (out.j && out.j.error) || "";
          if (e === "no_order") { throw new Error("We cannot find that order number. Check it against your confirmation email."); }
          if (e === "email_mismatch") { throw new Error("That email address does not match the one on this order."); }
          if (e === "too_large") { throw new Error("That photograph is too large even after resizing. Try another one."); }
          if (e === "bad_image") { throw new Error("That file could not be read as a photograph."); }
          throw new Error("The photograph was not received. Please try again, or email it to info@tamjump.com.");
        }
        done = true;
        send.textContent = "Sent";
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
