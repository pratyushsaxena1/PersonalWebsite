window.onload = function() {
    document.getElementById('userInput').focus();
};

window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        var myElement = document.getElementById('userInput');
        if (myElement) {
            myElement.focus();
            document.getElementById('userInput').focus();
        }
    }
});

function closePopup1() {
    document.getElementById('popupOverlay1').style.display = 'none';
}

function closePopup2() {
    document.getElementById('popupOverlay2').style.display = 'none';
}

window.onload = function() {
    const now = new Date();
    const formatted = now.toString().toLowerCase().split(' gmt')[0];
    document.getElementById('connectionTime').textContent = formatted;
};

// In Godaddy code, format it like '/homepage/experience', but in local environment, format it as '/experience'

function handleKeyDown(event) {
    const userInput = document.getElementById('userInput').value;
    if (event.key === 'Enter') {
        console.log('User entered:', userInput);
        switch (userInput.toLowerCase()) {
            case 'e':
                document.getElementById('userInput').value = '';
                window.location.href = '/experience';
                break;
            case 'g':
                document.getElementById('userInput').value = '';
                window.open('https://github.com/pratyushsaxena1', '_blank');
                break;
            case 'l':
                document.getElementById('userInput').value = '';
                window.open('https://www.linkedin.com/in/pratyush-saxena-735b81215/', '_blank');
                break;
            case 'p':
                document.getElementById('userInput').value = '';
                window.location.href = '/projects';
                break;
            case 'r':
                document.getElementById('userInput').value = '';
                window.location.href = '/resume';
                break;
            case 's':
                document.getElementById('userInput').value = '';
                window.open('https://open.spotify.com/user/31yu4lbmsbl5w3xdfawtcbnfrdfu?si=dd5f9a94a9d84721', '_blank');
                break;
            default:
                document.getElementById('userInput').value = '';
                break;
        }
        event.preventDefault();
    }
}