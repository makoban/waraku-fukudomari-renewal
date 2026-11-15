async (page) => {
  const browser = page.context().browser();
  const results = [];
  for (const width of [320, 360, 375, 390, 393, 412, 430, 768, 1024, 1440]) {
    const context = await browser.newContext({viewport: {width, height: 900}, deviceScaleFactor: width < 720 ? 2 : 1, reducedMotion: 'reduce'});
    const p = await context.newPage();
    const errors = [];
    p.on('pageerror', error => errors.push(error.message));
    await p.goto('http://127.0.0.1:8798/', {waitUntil: 'networkidle'});
    await p.evaluate(() => document.fonts.ready);
    await p.evaluate(async () => {
      for (let y = 0; y < document.documentElement.scrollHeight; y += 650) {
        scrollTo(0, y);
        await new Promise(resolve => setTimeout(resolve, 20));
      }
      scrollTo(0, 0);
    });
    await p.waitForLoadState('networkidle');
    const audit = await p.evaluate(() => {
      const visible = element => {
        const box = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        return box.width > 0 && box.height > 0 && style.visibility !== 'hidden' && style.display !== 'none' && !element.closest('dialog:not([open])');
      };
      const label = element => element.tagName.toLowerCase() + '.' + element.className;
      const overflow = [...document.querySelectorAll('body *')].filter(visible).filter(element => !element.closest('svg') && !element.classList.contains('sr-only') && !element.classList.contains('skip-link')).filter(element => {
        const box = element.getBoundingClientRect();
        return box.left < -1 || box.right > document.documentElement.clientWidth + 1;
      }).map(element => ({element: label(element), text: element.textContent.slice(0, 65)}));
      const selectors = '.hero-grid>*,.services-grid>*,.service-item>*,.conversation-grid>*,.access-grid>*,.photo-gallery>*,.info-list>div>*,.header-inner>*,.footer-grid>*,.primary-nav>a,.header-actions>*,.map-actions>*,.hero-actions>*,.contact-methods>*,.section-nav>a,.mobile-contact>a';
      const parentOverflow = [...document.querySelectorAll(selectors)].filter(visible).flatMap(element => {
        const box = element.getBoundingClientRect(), parent = element.parentElement, pb = parent.getBoundingClientRect(), style = getComputedStyle(parent);
        const left = pb.left + parseFloat(style.borderLeftWidth) + parseFloat(style.paddingLeft);
        const right = pb.right - parseFloat(style.borderRightWidth) - parseFloat(style.paddingRight);
        return box.left < left - 1 || box.right > right + 1 ? [{element: label(element), parent: label(parent), left: box.left, right: box.right, parentLeft: left, parentRight: right}] : [];
      });
      const phraseOverflow = [...document.querySelectorAll('.phrase,.keep')].filter(visible).flatMap(element => {
        const range = document.createRange();
        range.selectNodeContents(element);
        const text = range.getBoundingClientRect(), box = element.getBoundingClientRect();
        return text.width > box.width + 1 ? [{text: element.textContent, width: text.width, boxWidth: box.width}] : [];
      });
      const images = [...document.images].filter(element => !element.closest('dialog')).map(element => ({alt: element.alt, loaded: element.complete && element.naturalWidth > 0, src: element.currentSrc.split('/').pop(), width: element.naturalWidth, rendered: Math.round(element.getBoundingClientRect().width)}));
      const media = performance.getEntriesByType('resource').filter(entry => /\.(webp|png|jpg|svg|woff2)(\?|$)/.test(entry.name)).map(entry => ({file: entry.name.split('/').pop(), transferSize: entry.transferSize, encodedBodySize: entry.encodedBodySize}));
      return {viewport: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth, overflow, parentOverflow, phraseOverflow, images, media, mediaBytes: media.reduce((sum, entry) => sum + entry.encodedBodySize, 0)};
    });
    results.push({width, deviceScaleFactor: width < 720 ? 2 : 1, ...audit, errors});
    if (width === 390 || width === 1440) {
      await p.screenshot({path: '/tmp/waraku-verified-' + width + '.png', fullPage: true});
      await p.screenshot({path: '/tmp/waraku-top-' + width + '.png'});
    }
    await context.close();
  }
  return results;
}
