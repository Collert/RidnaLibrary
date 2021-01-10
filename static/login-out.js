// Sign in function to pass the user info to session
function onSignIn(googleUser){
    var id_token = googleUser.getAuthResponse().id_token;
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/login'); // Change the url after we move to our subdomain
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
        console.log('Signed in as: ' + googleUser.getBasicProfile().getName());
    };
    console.log(id_token);
    xhr.send('idtoken=' + id_token);
    //setTimeout(function(){window.location.href = "/";}, 1000);
}

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