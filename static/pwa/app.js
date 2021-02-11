// SW registration
var swRegistration = null;

if ('serviceWorker' in navigator) {
    navigator.serviceWorker
    .register('./service-worker.js')
    .then(function(registration) {
        console.log('Service Worker Registered!', registration);
        swRegistration = registration;
        return registration;
    })
    .catch(function(err) {
        console.error('Unable to register service worker.', err);
    });
}

// Notifications
document.addEventListener("DOMContentLoaded", () =>{
    const pushButton = document.getElementById('push-btn');

    if (Notification.permission == 'granted') {
        pushButton.hidden = true;
    }
    else {
        askPermission();
    }

    if (!("Notification" in window)) {
        pushButton.hidden = true;
    }

    pushButton.addEventListener('click', askPermission);

    function askPermission(evt) {
        pushButton.hidden = true;
    Notification.requestPermission().then(function(permission) {
        notificationButtonUpdate();
    });
    }

    function notificationButtonUpdate() {
    if (Notification.permission == 'granted') {
        pushButton.hidden = true;
    } else {
        pushButton.hidden = true;
    }
    }
});