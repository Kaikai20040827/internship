// Modern interactions for Apple-like UI

document.addEventListener('DOMContentLoaded', function () {
    // Reveal elements on scroll
    const reveals = document.querySelectorAll('.reveal');
    const options = { threshold: 0.1 };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, options);

    reveals.forEach(el => observer.observe(el));

    // Navbar shrink on scroll
    const nav = document.querySelector('.modern-navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 20) nav.classList.add('nav-scrolled');
        else nav.classList.remove('nav-scrolled');
    });

    // Hero parallax effect
    const hero = document.querySelector('.hero');
    if (hero) {
        hero.addEventListener('mousemove', e => {
            const rect = hero.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            hero.style.transform = `translate(${x * 6}px, ${y * 6}px)`;
        });
        hero.addEventListener('mouseleave', () => {
            hero.style.transform = '';
        });
    }

    // Upload progress placeholder: match forms that have an action containing 'upload'
    const uploadForms = document.querySelectorAll('form[enctype][action*="upload"]');
    uploadForms.forEach(form => {
        form.addEventListener('submit', e => {
            const progressWrap = document.createElement('div');
            progressWrap.className = 'upload-progress';
            const bar = document.createElement('div');
            bar.className = 'bar';
            progressWrap.appendChild(bar);
            form.appendChild(progressWrap);
            // Animate fake progress to show smoothness
            setTimeout(() => bar.style.width = '40%', 200);
            setTimeout(() => bar.style.width = '75%', 800);
            setTimeout(() => bar.style.width = '100%', 1500);
            // Remove progress bar after 3s to let server respond
            setTimeout(() => {
                if (progressWrap && progressWrap.parentNode) progressWrap.parentNode.removeChild(progressWrap);
            }, 3000);
        }, { once: true });
    });

    // Simple smooth scroll for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(a => {
        a.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) target.scrollIntoView({ behavior: 'smooth' });
        });
    });
});
