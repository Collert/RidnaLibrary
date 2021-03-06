var auth2;
// Sign in function to pass the user info to session
function onSignIn(googleUser){
    var id_token = googleUser.getAuthResponse().id_token;
    sessionStorage.setItem('token', id_token);
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/login');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
        console.log('Signed in as: ' + googleUser.getBasicProfile().getName());
    };
    console.log(id_token);
    xhr.send('idtoken=' + id_token);
    redirectPost("/login");
}

function redirectPost(url) {
    var form = document.createElement('form');
    document.body.appendChild(form);
    form.method = 'post';
    form.action = url;
    form.submit();
}

/**
 * Initializes the Sign-In client.
 */
var initClient = function() {
    gapi.load('auth2', function(){
        /**
         * Retrieve the singleton for the GoogleAuth library and set up the
         * client.
         */
        auth2 = gapi.auth2.init({
            client_id: '381057537277-pmtvd839t2a60eslm0bvke78rviilr5l.apps.googleusercontent.com'
        });

        // Attach the click handler to the sign-in button
        auth2.attachClickHandler('signin-button', {}, onSuccess, onFailure);
    });
};

/**
 * Handle successful sign-ins.
 */
var onSuccess = function() {
    const id_token = sessionStorage.getItem('token');
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/login');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.send('idtoken=' + id_token);
 };

/**
 * Handle sign-in failures.
 */
var onFailure = function(error) {
    console.log(error);
};

// Logout function
function signOut() {
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(function () {
      console.log('User signed out.');
    });
}

function onLoad() {
    gapi.load('auth2', function() {
      gapi.auth2.init();
    });
  }