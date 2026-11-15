async (page) => {
  const browser = page.context().browser();
  const output = '/Users/banmako/dev/アイアンドエフ/waraku-fukudomari-renewal/site/comparison/assets/png/';
  const screens = [
    {id:'home',title:'ホーム',before:'https://waraku-f.jp/',after:'https://makoban.github.io/waraku-fukudomari-renewal/'},
    {id:'rehabilitation',title:'充実のリハビリ',before:'https://waraku-f.jp/rehabilitation',after:'https://makoban.github.io/waraku-fukudomari-renewal/rehabilitation/'},
    {id:'dayservice',title:'デイサービス福泊',before:'https://waraku-f.jp/dayservice',after:'https://makoban.github.io/waraku-fukudomari-renewal/dayservice/'},
    {id:'cafe',title:'福泊カフェ',before:'https://waraku-f.jp/cafe',after:'https://makoban.github.io/waraku-fukudomari-renewal/cafe/'},
    {id:'careplan',title:'ケアプラン福泊',before:'https://waraku-f.jp/careplan',after:'https://makoban.github.io/waraku-fukudomari-renewal/careplan/'},
    {id:'recruit',title:'求人情報',before:'https://waraku-f.jp/#section04',after:'https://makoban.github.io/waraku-fukudomari-renewal/recruit/',beforeAnchor:'#section04'},
    {id:'blog',title:'スタッフブログ一覧',before:'https://waraku-f.jp/blog',after:'https://makoban.github.io/waraku-fukudomari-renewal/blog/'},
    {id:'company',title:'会社概要',before:'https://waraku-f.jp/company',after:'https://makoban.github.io/waraku-fukudomari-renewal/company/'},
    {id:'article',title:'ブログ記事（代表画面）',before:'https://waraku-f.jp/blog/843',after:'https://makoban.github.io/waraku-fukudomari-renewal/blog/843/'},
    {id:'archive',title:'月別一覧（代表画面）',before:'https://waraku-f.jp/blog/date/2023/11',after:'https://makoban.github.io/waraku-fukudomari-renewal/blog/date/2023/11/'}
  ];
  const modes = [
    {id:'desktop',width:1440,height:1000,dpr:1,mobile:false},
    {id:'mobile',width:390,height:844,dpr:2,mobile:true}
  ];
  const results = [];
  for (const mode of modes) {
    const context = await browser.newContext({viewport:{width:mode.width,height:mode.height},deviceScaleFactor:mode.dpr,isMobile:mode.mobile,hasTouch:mode.mobile,locale:'ja-JP',timezoneId:'Asia/Tokyo',colorScheme:'light',reducedMotion:'reduce'});
    const p = await context.newPage();
    for (const screen of screens) {
      for (const version of ['before','after']) {
        const response = await p.goto(screen[version],{waitUntil:'networkidle',timeout:30000});
        await p.evaluate(() => document.fonts.ready);
        if (version==='before' && screen.beforeAnchor) {
          await p.locator(screen.beforeAnchor).scrollIntoViewIfNeeded();
          await p.evaluate((selector) => window.scrollTo(0,document.querySelector(selector).getBoundingClientRect().top+scrollY),screen.beforeAnchor);
        } else {
          await p.evaluate(()=>scrollTo(0,0));
        }
        await p.evaluate(async()=>{
          const images=[...document.images].filter(e=>{const b=e.getBoundingClientRect();return b.width>0&&b.height>0&&b.top<innerHeight&&b.bottom>0&&!e.closest('dialog:not([open]),[hidden]');});
          await Promise.all(images.map(e=>e.decode().catch(()=>null)));
          await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
        });
        const filename=screen.id+'-'+mode.id+'-'+version+'.png';
        await p.screenshot({path:output+filename,fullPage:false,scale:'device'});
        results.push({id:screen.id,screen:screen.title,version,mode:mode.id,url:p.url(),status:response.status(),capture_file:'site/comparison/assets/png/'+filename,viewport:{width:mode.width,height:mode.height},devicePixelRatio:mode.dpr,capturedAt:new Date().toISOString(),...await p.evaluate(()=>({pageTitle:document.title,viewportMeta:document.querySelector('meta[name="viewport"]')?.content,layoutViewportWidth:innerWidth,layoutViewportHeight:innerHeight,visualScale:visualViewport?.scale,scrollX,scrollY,visibleImageFailures:[...document.images].filter(e=>{const b=e.getBoundingClientRect();return b.width>0&&b.height>0&&b.top<innerHeight&&b.bottom>0&&!e.closest('dialog:not([open]),[hidden]')&&(!e.complete||!e.naturalWidth);}).map(e=>e.currentSrc||e.getAttribute('src'))}))});
      }
    }
    await context.close();
  }
  return results;
}
