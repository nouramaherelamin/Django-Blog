document.addEventListener('DOMContentLoaded', function() {
    console.log('Blog loaded successfully!');
    
    // --- Dark Mode Toggle ---
    const themeToggleBtn = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    const themeIcon = document.getElementById('theme-icon');

    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    htmlElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            htmlElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }

    function updateThemeIcon(theme) {
        if (!themeIcon) return;
        if (theme === 'dark') {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        } else {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
        }
    }

    // --- Navbar Scroll Effect ---
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 10) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // --- Intersection Observer for Scroll Animations ---
    const revealElements = document.querySelectorAll('.reveal-up');
    
    const revealOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const revealOnScroll = new IntersectionObserver(function(entries, observer) {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add('active');
            
            // Trigger counter animation if it's a stat card
            const counters = entry.target.querySelectorAll('.counter-value');
            if (counters.length > 0) {
                animateCounters(counters);
            }
            
            observer.unobserve(entry.target);
        });
    }, revealOptions);

    revealElements.forEach(el => {
        revealOnScroll.observe(el);
    });

    // --- Counter Animation ---
    function animateCounters(counters) {
        counters.forEach(counter => {
            const target = +counter.getAttribute('data-target');
            const duration = 1500; // ms
            const increment = target / (duration / 16); // 60fps
            
            let current = 0;
            const updateCounter = () => {
                current += increment;
                if (current < target) {
                    counter.innerText = Math.ceil(current);
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.innerText = target;
                }
            };
            updateCounter();
        });
    }

    // --- Auto-hide alerts ---
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert) {
                alert.classList.remove('show');
                setTimeout(function() {
                    alert.remove();
                }, 150);
            }
        }, 5000);
    });
    
    // --- Smooth scroll for anchor links ---
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if(targetId === '#') return;
            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // --- Grid / List View Toggle ---
    const btnGrid = document.getElementById('btn-grid');
    const btnList = document.getElementById('btn-list');
    const postsContainer = document.getElementById('posts-container');
    
    if (btnGrid && btnList && postsContainer) {
        const viewPref = localStorage.getItem('blogViewPref') || 'grid';
        
        const setView = (view) => {
            if (view === 'list') {
                postsContainer.classList.add('list-view');
                btnList.classList.add('active');
                btnList.classList.replace('btn-outline-primary', 'btn-primary');
                btnGrid.classList.remove('active');
                btnGrid.classList.replace('btn-primary', 'btn-outline-primary');
            } else {
                postsContainer.classList.remove('list-view');
                btnGrid.classList.add('active');
                btnGrid.classList.replace('btn-outline-primary', 'btn-primary');
                btnList.classList.remove('active');
                btnList.classList.replace('btn-primary', 'btn-outline-primary');
            }
            localStorage.setItem('blogViewPref', view);
        };
        
        setView(viewPref);
        
        btnGrid.addEventListener('click', () => setView('grid'));
        btnList.addEventListener('click', () => setView('list'));
    }

});