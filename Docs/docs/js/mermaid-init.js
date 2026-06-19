document$.subscribe(() => {
  const isDark = document.documentElement.classList.contains('dark');

  mermaid.initialize({
    startOnLoad: true,
    theme: isDark ? 'dark' : 'default',
    themeVariables: {
      fontFamily: 'Inter, Roboto, sans-serif',
      primaryColor: isDark ? '#F48FB1' : '#BA68C8',
      edgeLabelBackground: '#ffffff',
      background: isDark ? 'transparent' : '#ffffff',
    }
  });

  mermaid.init(undefined, document.querySelectorAll('.language-mermaid'));
});
