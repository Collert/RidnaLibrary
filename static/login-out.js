var auth2;
// Sign in function to pass the user info to session
function onSignIn(response){
    const responsePayload = decodeJwtResponse(response.credential);
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/login');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
        console.log('Signed in as: ' + responsePayload.name);
    };
    console.log(responsePayload);
    if (responsePayload.hasOwnProperty('picture') == false){
        responsePayload.picture == "none";
    }
    xhr.send('id=' + responsePayload.sub + '&email=' + responsePayload.email + '&first=' + responsePayload.given_name + '&last=' + responsePayload.family_name + '&pic=' + responsePayload.picture);
    //xhr.send('email=' + responsePayload.email);
    //xhr.send('first=' + responsePayload.given_name);
    //xhr.send('last=' + responsePayload.family_name);
    //xhr.send('pic=' + responsePayload.picture);
    setTimeout(() => {
        window.location.replace("/");
    }, 2000);
}

function decodeJwtResponse (token) {
    var base64Url = token.split('.')[1];
    var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    var jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
};

/*function redirectPost(url) {
    var form = document.createElement('form');
    document.body.appendChild(form);
    form.method = 'post';
    form.action = url;
    form.submit();
}
*/

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
    setTimeout(() => {
        window.location.replace("/");
    }, 2000);
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
