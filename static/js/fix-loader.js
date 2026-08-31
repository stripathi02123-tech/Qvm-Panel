// Emergency fix to clear stuck loader
setTimeout(() => {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.remove();
        console.log('Stuck loader removed');
    }
}, 100);

// Also clear any existing loader immediately
document.addEventListener('DOMContentLoaded', () => {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.remove();
        console.log('Stuck loader removed on DOM load');
    }
});
