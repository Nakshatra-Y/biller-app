document.addEventListener("DOMContentLoaded", () => {
  const flashes = document.querySelectorAll(".flash");
  if (flashes.length) {
    setTimeout(() => {
      flashes.forEach((f) => (f.style.display = "none"));
    }, 3500);
  }

  const toastContainerId = "toastContainer";
  let toastContainer = document.getElementById(toastContainerId);
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = toastContainerId;
    toastContainer.className = "toast-container";
    document.body.appendChild(toastContainer);
  }

  window.showToast = function (message, type = "info") {
    const toast = document.createElement("div");
    toast.className = "toast toast-" + type;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.classList.add("hide");
      setTimeout(() => toast.remove(), 400);
    }, 2800);
  };

  const notificationContainer = document.getElementById("notification-container");
  if (!notificationContainer) return;

  window.showNotification = function (message, type, options) {
    type = type || "info";
    const duration = (options && options.duration) || 4000;
    const node = document.createElement("div");
    node.className = "notification notification-" + type + " notification-enter";
    const text = document.createElement("span");
    text.className = "notification-text";
    text.textContent = message;
    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "notification-close";
    closeBtn.setAttribute("aria-label", "Close");
    closeBtn.innerHTML = "&#10005;";
    node.appendChild(text);
    node.appendChild(closeBtn);
    notificationContainer.appendChild(node);

    function remove() {
      node.classList.add("notification-leave");
      setTimeout(() => {
        if (node.parentNode) node.parentNode.removeChild(node);
      }, 300);
    }

    closeBtn.addEventListener("click", remove);
    const t = setTimeout(remove, duration);
    node._clearNotif = () => clearTimeout(t);
  };
});

