// Professional Academic Website JavaScript for ICDAR 2026 Competition

// Smooth scrolling for navigation links
document.addEventListener('DOMContentLoaded', function() {
    // Handle navigation link clicks
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                const headerHeight = document.querySelector('.header').offsetHeight;
                const targetPosition = targetSection.offsetTop - headerHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Highlight active navigation item on scroll
    function updateActiveNavigation() {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('.nav-link');
        const headerHeight = document.querySelector('.header').offsetHeight;
        const scrollPosition = window.scrollY + headerHeight + 100;
        
        let currentSection = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                currentSection = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.style.borderBottomColor = 'transparent';
            if (link.getAttribute('href') === '#' + currentSection) {
                link.style.borderBottomColor = '#fff5eb';
            }
        });
    }
    
    // Listen for scroll events
    window.addEventListener('scroll', updateActiveNavigation);
    
    // Initial call to set active navigation
    updateActiveNavigation();
    
    // Download button interactions
    const downloadButtons = document.querySelectorAll('.btn-download');
    
    downloadButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                // In a real implementation, this would trigger actual downloads
                alert('Download would start here. Files are not yet available.');
            } else {
                alert('This dataset component is not yet available. Please check the schedule for release dates.');
            }
        });
    });
    
    // Email links interaction
    const emailLinks = document.querySelectorAll('a[href^="mailto:"]');
    
    emailLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Allow default email client to open
            console.log('Opening email client for:', this.getAttribute('href'));
        });
    });
    
    // External links - ensure they open in new tabs
    const externalLinks = document.querySelectorAll('a[target="_blank"]');
    
    externalLinks.forEach(link => {
        link.addEventListener('click', function() {
            console.log('Opening external link:', this.href);
        });
    });
    
    // Add loading state for future dynamic content
    function showLoading(element) {
        element.innerHTML = '<span style="color: #666;">Loading...</span>';
    }
    
    function hideLoading(element, originalContent) {
        element.innerHTML = originalContent;
    }
    
    // Intersection Observer for animation on scroll (optional enhancement)
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for scroll animations
    const animatedElements = document.querySelectorAll('.track, .metric, .team-member, .timeline-item');
    
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Table responsiveness helper
    function makeTablesResponsive() {
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            if (window.innerWidth < 768) {
                table.style.fontSize = '0.9rem';
            } else {
                table.style.fontSize = '1rem';
            }
        });
    }
    
    window.addEventListener('resize', makeTablesResponsive);
    makeTablesResponsive();
    
    // Copy functionality for CSV examples
    const csvExamples = document.querySelectorAll('.csv-example code, .example code');
    
    csvExamples.forEach(code => {
        code.style.cursor = 'pointer';
        code.title = 'Click to copy';
        
        code.addEventListener('click', function() {
            const text = this.textContent;
            
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(() => {
                    showTooltip(this, 'Copied!');
                });
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showTooltip(this, 'Copied!');
            }
        });
    });
    
    // Simple tooltip function
    function showTooltip(element, message) {
        const tooltip = document.createElement('div');
        tooltip.textContent = message;
        tooltip.style.position = 'absolute';
        tooltip.style.background = '#ff2a19';
        tooltip.style.color = 'white';
        tooltip.style.padding = '0.5rem';
        tooltip.style.borderRadius = '4px';
        tooltip.style.fontSize = '0.8rem';
        tooltip.style.zIndex = '1000';
        tooltip.style.pointerEvents = 'none';
        
        const rect = element.getBoundingClientRect();
        tooltip.style.top = (rect.top - 40 + window.scrollY) + 'px';
        tooltip.style.left = (rect.left + rect.width / 2 - 25) + 'px';
        
        document.body.appendChild(tooltip);
        
        setTimeout(() => {
            if (tooltip.parentNode) {
                tooltip.parentNode.removeChild(tooltip);
            }
        }, 2000);
    }
    
    // Print page functionality
    function addPrintStyles() {
        const printStyles = `
            @media print {
                .header { display: none; }
                .footer { display: none; }
                main { margin-top: 0; }
                .hero { background: white !important; color: black !important; }
                * { box-shadow: none !important; }
            }
        `;
        
        const styleSheet = document.createElement('style');
        styleSheet.textContent = printStyles;
        document.head.appendChild(styleSheet);
    }
    
    addPrintStyles();
    
    // Console welcome message
    console.log('%cICDAR 2026 AnyScript Competition', 'color: #ff2a19; font-size: 20px; font-weight: bold;');
    console.log('%cWebsite loaded successfully. Good luck with your submissions!', 'color: #ff2a19; font-size: 14px;');
});