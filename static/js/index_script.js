(function () {
    // bare-name commands that open external links or navigate. Use `cd <dir>` for
    // actual directories (experience/projects/resume).
    const ROUTES = {
        classic: { kind: 'route', target: '/classic' },
        home: { kind: 'route', target: '/' },
        exit: { kind: 'route', target: '/' },
        logout: { kind: 'route', target: '/' },
        tools: { kind: 'external', target: 'https://tools.pratyushsaxena.com' },
        pro: { kind: 'external', target: 'https://pro.pratyushsaxena.com' },
        github: { kind: 'external', target: 'https://github.com/pratyushsaxena1' },
        linkedin: { kind: 'external', target: 'https://www.linkedin.com/in/pratyush-saxena-735b81215/' },
        spotify: { kind: 'external', target: 'https://open.spotify.com/user/31yu4lbmsbl5w3xdfawtcbnfrdfu?si=dd5f9a94a9d84721' },
    };

    const JOKES = [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "There are 10 kinds of people: those who understand binary, and those who don't.",
        "I would tell you a UDP joke, but you might not get it.",
        "Why did the developer go broke? Because he used up all his cache.",
        "A SQL query walks into a bar, walks up to two tables, and asks: 'mind if I join you?'",
        "I've got a really good UDP joke to tell you, but I'm not sure you'll get it.",
        "There's no place like 127.0.0.1.",
        "Why do Java developers wear glasses? Because they don't C#.",
    ];

    const FORTUNES = [
        "Code is read more often than it is written. - Guido van Rossum",
        "Premature optimization is the root of all evil. - Donald Knuth",
        "First, solve the problem. Then, write the code. - John Johnson",
        "Talk is cheap. Show me the code. - Linus Torvalds",
        "Simplicity is prerequisite for reliability. - Edsger Dijkstra",
        "Make it work, make it right, make it fast. - Kent Beck",
        "Programming isn't about what you know; it's about what you can figure out.",
    ];

    const NEOFETCH_ART = [
        "       .-.        ",
        "      / o \\       ",
        "     |  ^  |      ",
        "      \\___/       ",
        "      /| |\\       ",
        "     / | | \\      ",
        "                  ",
    ];

    const COMMANDS = {
        help: () => [
            'file system:',
            '  ls [flags] [path]        list files and directories',
            '  cd [dir]                 change directory  (e.g. cd projects, cd ..)',
            '  cat <file> [<file>...]   print file contents',
            '  open <file|link>         open a binary or link in a new tab',
            '  tree [path]              recursive directory listing',
            '  pwd                      print working directory',
            '  clear                    clear the screen',
            '',
            'session:',
            '  whoami                   print current user',
            '  date                     print the current date',
            '  echo <text>              print text',
            '  history                  show command history',
            '  man <cmd>                show the manual page for a command',
            '  help                     show this list',
            '  exit | logout            end session, return to landing',
            '',
            'navigation:',
            '  classic                  switch to the classic website view',
            '  home                     return to the landing page',
            '  tools                    open my free online tools (new tab)',
            '  pro                      open my paid tools for businesses (new tab)',
            '  github                   open my github profile in a new tab',
            '  linkedin                 open my linkedin profile in a new tab',
            '  spotify                  open my spotify in a new tab',
            '  email | mail             print my email (click to open mail app)',
            '',
            'for more about me, try `cd about` (or `cat about/bio.txt`)',
            '',
            'extras:',
            '  neofetch                 system info, terminal-style',
            '  top | ps                 see what is really running',
            '  theme [name]             change color scheme (green/amber/mono/solarized)',
            '  joke                     tell a joke',
            '  fortune                  a programming quote',
            '  matrix                   wake up neo',
            '  snake                    play snake',
            '  spiderman | spidey       with great power...',
            '  sudo <anything>          (you are not in sudoers)',
            '',
            'keyboard:',
            '  tab                      autocomplete commands and file/dir names',
            '  up / down                step through command history',
            '  ctrl+c                   cancel current input',
            '  ctrl+l                   clear the screen',
        ],
        email: () => '__EMAIL__',
        mail: () => '__EMAIL__',
        whoami: () => ['amazingvisitor'],
        pwd: () => ['/home/amazingvisitor'],
        history: () => '__HISTORY__',
        date: () => [new Date().toString().toLowerCase()],
        joke: () => [pick(JOKES)],
        fortune: () => [pick(FORTUNES)],
        neofetch: () => [
            '       .-.       amazingvisitor@pratyushsaxenawebsite',
            '      / o \\      -----------------------------------',
            '     |  ^  |     OS:       BrowserOS ' + (navigator.userAgent.includes('Mac') ? '(macOS-flavored)' : ''),
            '      \\___/      Host:     ' + window.location.hostname,
            '      /| |\\      Shell:    pratyush.sh 4.0',
            '     / | | \\     Theme:    green-on-black',
            '                  Editor:   vim, obviously',
            '                  Uptime:   ' + Math.floor(performance.now() / 1000) + 's in this session',
            '                  CPU:      Cornell CS + AI',
            '                  Memory:   too much coffee',
        ],
        spiderman: () => '__SPIDERMAN__',
        spidey: () => '__SPIDERMAN__',
        top: () => TOP_LINES,
        ps: () => TOP_LINES,
        matrix: () => '__MATRIX__',
        snake: () => '__SNAKE__',
        clear: () => '__CLEAR__',
    };

    const TOP_LINES = [
        'PID    USER          %CPU  %MEM  TIME       COMMAND',
        '4096   pratyush      98.2  64.0  ∞          coding.exe',
        '4097   pratyush      42.3  21.5  6h         cs-classes',
        '4098   pratyush      78.1  35.2  ∞          building-things',
        '4099   pratyush      15.0  10.5  3h         late-night-drives',
        '4100   pratyush      12.5   8.0  ∞          guitar-practice',
        '4101   pratyush      99.9  51.0  ∞          caffeine.daemon',
        '4102   waffle         4.2   2.1  24h        sleeping',
        '4103   pratyush      22.7  18.3  2h         basketball',
        '4104   pratyush       0.1   0.1  0.05s      reading-this',
    ];

    // pixel-art chibi spider-man rendered as a 15×23 grid of inline-block divs,
    // so every pixel is a guaranteed square regardless of font. characters:
    //   k = black outline, r = red mask/torso/feet, b = blue legs/belt,
    //   w = white eyes, . = transparent.
    const SPIDERMAN_PIXELS = [
        '......kkk......',
        '.....krrrk.....',
        '....krrrrrk....',
        '...krrrrrrrk...',
        '..krwwwrwwwrk..',
        '.krwwwwrwwwwrk.',
        '.krwwwwrwwwwrk.',
        '..krwwwrwwwrk..',
        '...krrrrrrrk...',
        '....krrrrrk....',
        '.....krrrk.....',
        '....krrrrrk....',
        '..krrrrrrrrrk..',
        '.krrrrrrrrrrrk.',
        '.krrrrrrrrrrrk.',
        '.krrrrrrrrrrrk.',
        '..krrrrrrrrrk..',
        '..kbbbbbbbbbk..',
        '..kbbk...kbbk..',
        '..kbbk...kbbk..',
        '..kbbk...kbbk..',
        '..krrk...krrk..',
        '..kkkk...kkkk..',
    ];

    const PIXEL_PALETTE = {
        k: '#0a0a0a',
        r: '#e62429',
        b: '#1e88e5',
        w: '#ffffff',
    };
    const PIXEL_SIZE = 12; // px per pixel - bumps the figure to a comfortable size

    function buildPixelArt(rows, palette, size) {
        const wrap = document.createElement('div');
        wrap.style.padding = '0.4em 0';
        for (const row of rows) {
            const rowDiv = document.createElement('div');
            rowDiv.style.lineHeight = '0';
            rowDiv.style.fontSize = '0';
            for (const ch of row) {
                const px = document.createElement('span');
                px.style.display = 'inline-block';
                px.style.width = size + 'px';
                px.style.height = size + 'px';
                const color = palette[ch];
                if (color) px.style.background = color;
                rowDiv.appendChild(px);
            }
            wrap.appendChild(rowDiv);
        }
        return wrap;
    }

    // ---------- virtual filesystem ----------
    // Tree under ~. Entry types: 'file' (cat-able), 'dir' (cd-able), 'link' (URL),
    // 'binary' (download URL - cat says it's binary).
    function slugify(s) {
        return String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    }

    function buildVFS() {
        const exp = (window.SITE && window.SITE.experience) || [];
        const projs = (window.SITE && window.SITE.projects) || [];
        const root = { type: 'dir', entries: {} };

        // ~/README.md - the entry point at root
        root.entries['README.md'] = { type: 'file', content: [
            "Welcome to my terminal portfolio. I'm Pratyush, a CS + AI student at Cornell. I interned at Cisco (Splunk) this past summer; before that, at NASA, Biostate AI, and Alpheva AI.",
            "",
            "How to navigate this website:",
            "  cat <file>     read a file       (e.g. cat about/bio.txt)",
            "  cd <folder>    enter a folder    (e.g. cd projects)",
            "  <link name>    open a link       (e.g. github)",
            "",
            "Type `help` for the full command list, or `tree` for a map of everything.",
        ]};

        // ~/about/  - personal info files
        const aboutDir = { type: 'dir', entries: {} };
        aboutDir.entries['bio.txt'] = { type: 'file', content: [
            "I'm a Cornell student pursuing a bachelor's degree in Computer Science with a minor in Artificial Intelligence.",
            "",
            "I've interned at NASA, Biostate AI, and Alpheva AI, gaining experience across software engineering, AI research, and fintech. This past summer I was in San Jose interning at Cisco (Splunk) on security and automation engineering.",
            "",
            "Outside of CS: late-night drives, music (any genre), guitar, my dog Waffle, and basketball.",
            "",
            "Always excited to learn new things and meet people doing interesting work. Feel free to reach out.",
        ]};
        aboutDir.entries['now.txt'] = { type: 'file', content: [
            "What I'm up to right now:",
            "",
            "  - Studying CS + AI at Cornell",
            "  - Back in Ithaca after a summer at Cisco (Splunk) on security & automation",
            "  - Shipping side projects in computer vision and ML",
            "  - Picking up guitar again, slowly",
            "  - Member of Cornell's Generative AI Club and ACSU",
        ]};
        aboutDir.entries['stack.txt'] = { type: 'file', content: [
            "Things I've worked with:",
            "",
            "Languages    Python, Java, Go, JavaScript, SQL, HTML/CSS",
            "Frameworks   Flask, React, React Native",
            "ML / CV      OpenCV, NumPy, CNNs",
            "Other        phpMyAdmin, Onshape, ArcGIS, Excel, Git",
            "",
            "Most comfortable in Python; the rest comes and goes depending on the project.",
        ], preserveSpaces: true };
        aboutDir.entries['interests.txt'] = { type: 'file', content: [
            "Late-night drives",
            "Music (any genre)",
            "Guitar",
            "Waffle (my dog)",
            "Basketball",
            "Building things",
        ]};
        aboutDir.entries['playlist.txt'] = { type: 'file', content: [
            "Currently in rotation:",
            "",
            "  - Late-night driving playlists (any genre, low BPM)",
            "  - Some Hindi / Bollywood mixed in",
            "  - A lot of indie, R&B, and hip-hop",
            "",
            "For the actual real-time list, type `spotify` to open mine.",
        ]};
        aboutDir.entries['hook.txt'] = { type: 'file', content: [
            (window.SITE && window.SITE.hook) || '',
        ]};
        root.entries['about'] = aboutDir;

        // ~/projects/<slug>.md
        const projectsDir = { type: 'dir', entries: {} };
        for (const p of projs) {
            const content = [
                '# ' + p.name + (p.subtitle ? ' - ' + p.subtitle : ''),
                '',
                p.description,
                '',
                'tags: ' + (p.tags || []).join(', '),
            ];
            if (p.links && p.links.length) {
                content.push('link: ' + p.links.map(l => l.href).join('  '));
            }
            projectsDir.entries[slugify(p.name) + '.md'] = {
                type: 'file',
                content,
            };
        }
        root.entries['projects'] = projectsDir;

        // ~/experience/<slug>.md
        const expDir = { type: 'dir', entries: {} };
        for (const e of exp) {
            expDir.entries[slugify(e.company) + '.md'] = {
                type: 'file',
                content: [
                    '# ' + e.company + ' - ' + e.role,
                    '## ' + e.dates,
                    '',
                    e.description,
                    '',
                    'tags: ' + (e.tags || []).join(', '),
                ],
            };
        }
        root.entries['experience'] = expDir;

        // ~/links/  - external links collected here
        root.entries['links'] = { type: 'dir', entries: {
            'github':   { type: 'link', url: 'https://github.com/pratyushsaxena1' },
            'linkedin': { type: 'link', url: 'https://www.linkedin.com/in/pratyush-saxena-735b81215/' },
            'spotify':  { type: 'link', url: 'https://open.spotify.com/user/31yu4lbmsbl5w3xdfawtcbnfrdfu?si=dd5f9a94a9d84721' },
        }};

        root.entries['resume.pdf'] = { type: 'binary', url: '/resume.pdf' };

        return root;
    }

    const VFS = buildVFS();

    // current working directory as path-segment array; root is ['~'].
    let cwd = ['~'];

    // resolve `input` (relative or absolute-ish) to a path segments array.
    // supports: 'projects', '../experience', '~/foo', '~', '..', '.', 'a/b/c'
    function resolvePath(input) {
        if (input === undefined || input === null || input === '') return cwd.slice();
        if (input === '~' || input === '/' || input === 'home') return ['~'];
        let segs;
        if (input.startsWith('~/')) {
            segs = ['~'];
            for (const part of input.slice(2).split('/')) {
                if (part === '' || part === '.') continue;
                if (part === '..') { if (segs.length > 1) segs.pop(); continue; }
                segs.push(part);
            }
        } else if (input.startsWith('/')) {
            segs = ['~']; // we don't model / above home
            for (const part of input.split('/')) {
                if (part === '' || part === '.') continue;
                if (part === '..') { if (segs.length > 1) segs.pop(); continue; }
                segs.push(part);
            }
        } else {
            segs = cwd.slice();
            for (const part of input.split('/')) {
                if (part === '' || part === '.') continue;
                if (part === '..') { if (segs.length > 1) segs.pop(); continue; }
                segs.push(part);
            }
        }
        return segs;
    }

    function getNode(segments) {
        if (!segments || segments.length === 0 || segments[0] !== '~') return null;
        let node = VFS;
        for (let i = 1; i < segments.length; i++) {
            if (!node || node.type !== 'dir') return null;
            const child = node.entries[segments[i]];
            if (!child) return null;
            node = child;
        }
        return node;
    }

    function pathDisplay(segments) { return segments.join('/'); }
    function pathPwd(segments) {
        return segments.length === 1
            ? '/home/amazingvisitor'
            : '/home/amazingvisitor/' + segments.slice(1).join('/');
    }
    function listEntries(segments, opts) {
        const node = getNode(segments);
        if (!node || node.type !== 'dir') return [];
        let names = Object.keys(node.entries);
        if (opts && opts.dirsOnly) names = names.filter(n => node.entries[n].type === 'dir');
        if (opts && opts.filesOnly) names = names.filter(n => node.entries[n].type !== 'dir');
        return names;
    }

    // split argv-style: separate flags (-x, --foo) from positionals.
    function parseArgs(s) {
        const tokens = (s || '').trim().split(/\s+/).filter(Boolean);
        const flags = [], positional = [];
        for (const t of tokens) (t.startsWith('-') ? flags : positional).push(t);
        return { flags, positional };
    }

    function makePromptHtml() {
        return '<span class="user">amazingvisitor</span>' +
            '<span class="at">@</span>' +
            '<span class="host">pratyushsaxenawebsite</span> ' +
            `<span class="path">${escapeHTML(pathDisplay(cwd))}</span> ` +
            '<span class="sigil">%</span> ';
    }

    function updatePromptPath() {
        const el = $('promptPath');
        if (el) el.textContent = pathDisplay(cwd);
    }

    const history = [];
    let historyIdx = -1;
    let draft = '';

    function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
    function $(id) { return document.getElementById(id); }

    function lastLoginString() {
        const d = new Date();
        const date = d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
        const time = d.toTimeString().slice(0, 8);
        return `${date} ${time}`;
    }

    function focusInput() {
        const i = $('userInput');
        if (i) i.focus();
    }

    function clearScreen() {
        const intro = $('intro');
        const out = $('terminalOutput');
        if (intro) intro.innerHTML = '';
        if (out) out.innerHTML = '';
        const banner = document.querySelector('.ascii-banner');
        if (banner) banner.style.display = 'none';
    }

    function escapeHTML(s) {
        return s.replace(/[&<>"']/g, c => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[c]));
    }

    // Render a text line into `p`, turning any http(s) URLs into clickable
    // anchors. Non-URL text is added as safe text nodes (no innerHTML).
    function appendLinkified(p, line) {
        const re = /(https?:\/\/[^\s]+)/g;
        let last = 0, m;
        while ((m = re.exec(line)) !== null) {
            if (m.index > last) {
                p.appendChild(document.createTextNode(line.slice(last, m.index)));
            }
            const a = document.createElement('a');
            a.href = m[0];
            a.textContent = m[0];
            a.target = '_blank';
            a.rel = 'noopener';
            p.appendChild(a);
            last = m.index + m[0].length;
        }
        if (last < line.length) {
            p.appendChild(document.createTextNode(line.slice(last)));
        }
    }

    function appendBlock(rawCmd, lines, opts) {
        const out = $('terminalOutput');
        if (!out) return;
        const wrap = document.createElement('div');

        if (rawCmd !== null) {
            const echo = document.createElement('p');
            echo.className = 'input-line';
            echo.innerHTML = makePromptHtml() + escapeHTML(rawCmd);
            wrap.appendChild(echo);
        }

        if (Array.isArray(lines)) {
            for (const line of lines) {
                const p = document.createElement('p');
                p.className = 'computer-text';
                if (opts && opts.preserveSpaces) p.style.whiteSpace = 'pre';
                appendLinkified(p, line);
                wrap.appendChild(p);
            }
        }
        out.appendChild(wrap);
        // keep the input row visible: scroll to the bottom of the page
        requestAnimationFrame(() => {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        });
    }

    function appendNodes(rawCmd, nodes) {
        const out = $('terminalOutput');
        if (!out) return;
        const wrap = document.createElement('div');
        const echo = document.createElement('p');
        echo.className = 'input-line';
        echo.innerHTML = makePromptHtml() + escapeHTML(rawCmd);
        wrap.appendChild(echo);
        for (const node of nodes) wrap.appendChild(node);
        out.appendChild(wrap);
        requestAnimationFrame(() => {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        });
    }

    let matrixActive = false;
    function runMatrix() {
        matrixActive = true;
        const input = $('userInput');
        if (input) input.blur();
        const overlay = document.createElement('div');
        overlay.id = 'matrix-overlay';
        Object.assign(overlay.style, {
            position: 'fixed',
            top: '0',
            right: '0',
            bottom: '0',
            left: '0',
            background: '#000',
            zIndex: '2147483647',
            cursor: 'pointer',
        });

        const canvas = document.createElement('canvas');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        canvas.style.display = 'block';
        overlay.appendChild(canvas);

        const hint = document.createElement('div');
        hint.textContent = 'click anywhere or press any key to exit';
        Object.assign(hint.style, {
            position: 'absolute',
            bottom: '1.5em',
            left: 0,
            right: 0,
            textAlign: 'center',
            color: '#02e35c',
            fontFamily: 'Menlo, monospace',
            fontSize: '0.85em',
            letterSpacing: '0.1em',
            opacity: '0.7',
            pointerEvents: 'none',
        });
        overlay.appendChild(hint);

        document.body.appendChild(overlay);

        const ctx = canvas.getContext('2d');
        const fontSize = 16;
        const cols = Math.floor(canvas.width / fontSize);
        const rows = Math.ceil(canvas.height / fontSize);
        // scatter drops across the visible area so chars are on screen immediately,
        // with some starting just above so new streaks keep cascading in.
        const drops = new Array(cols).fill(0).map(() => Math.random() * rows - 10);
        const chars = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎ0123456789Z@#$%^&*';

        let raf;
        function draw() {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.08)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#02e35c';
            ctx.font = fontSize + 'px Menlo, monospace';
            for (let i = 0; i < drops.length; i++) {
                const ch = chars[Math.floor(Math.random() * chars.length)];
                ctx.fillText(ch, i * fontSize, drops[i] * fontSize);
                if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
                drops[i]++;
            }
            raf = requestAnimationFrame(draw);
        }
        draw();

        function exit() {
            cancelAnimationFrame(raf);
            overlay.remove();
            document.removeEventListener('keydown', exit);
            matrixActive = false;
            focusInput();
        }
        overlay.addEventListener('click', exit);
        // defer the exit listener by one tick so the same Enter keypress that started
        // matrix (held / repeated) can't immediately dismiss the overlay
        setTimeout(() => document.addEventListener('keydown', exit), 0);
    }

    // ---------- themes ----------
    const THEMES = ['green', 'amber', 'mono', 'solarized'];
    let currentTheme = 'green';
    function setTheme(name) {
        if (!THEMES.includes(name)) name = 'green';
        currentTheme = name;
        document.body.classList.remove(...THEMES.map(t => 'theme-' + t));
        document.body.classList.add('theme-' + name);
        try { localStorage.setItem('terminalTheme', name); } catch (e) {}
    }
    function loadTheme() {
        let saved = null;
        try { saved = localStorage.getItem('terminalTheme'); } catch (e) {}
        setTheme(saved && THEMES.includes(saved) ? saved : 'green');
    }

    // ---------- man pages ----------
    const MAN_PAGES = {
        ls: [
            'NAME',
            '       ls - list directory contents',
            '',
            'SYNOPSIS',
            '       ls [flags] [path]',
            '',
            'DESCRIPTION',
            '       Lists files and directories in path (or current dir).',
            '       Flag arguments are accepted but ignored.',
        ],
        cd: [
            'NAME',
            '       cd - change directory',
            '',
            'SYNOPSIS',
            '       cd [dir]',
            '',
            'DESCRIPTION',
            '       Change the current working directory.',
            '       With no argument, returns home (~). `cd ..` goes to parent.',
            '       `cd ~` and `cd /` and `cd home` all return home.',
        ],
        cat: [
            'NAME',
            '       cat - concatenate and print files',
            '',
            'SYNOPSIS',
            '       cat <file> [<file>...]',
            '',
            'DESCRIPTION',
            '       Print one or more files. Errors with "Is a directory" or',
            '       "No such file or directory" appropriately. Multiple files',
            '       are concatenated.',
        ],
        pwd: [
            'NAME',
            '       pwd - print working directory',
            '',
            'SYNOPSIS',
            '       pwd',
        ],
        tree: [
            'NAME',
            '       tree - recursive directory listing',
            '',
            'SYNOPSIS',
            '       tree [path]',
            '',
            'DESCRIPTION',
            '       Print a tree-shaped view of the directory and all subdirectories.',
        ],
        open: [
            'NAME',
            '       open - open a file with its default handler',
            '',
            'SYNOPSIS',
            '       open <file>',
            '',
            'DESCRIPTION',
            '       For binary files (resume.pdf), opens / downloads in a new tab.',
            '       For links (github, linkedin, spotify), opens the URL in a new tab.',
            '       For text files, prints contents (like cat).',
        ],
        history: [
            'NAME',
            '       history - show command history',
            '',
            'SYNOPSIS',
            '       history',
        ],
        echo: [
            'NAME',
            '       echo - print text',
            '',
            'SYNOPSIS',
            '       echo <text>',
        ],
        clear: [
            'NAME',
            '       clear - clear the terminal screen',
            '',
            'SYNOPSIS',
            '       clear',
            '',
            'DESCRIPTION',
            '       Removes all visible output. Ctrl+L is the keyboard shortcut.',
        ],
        whoami: [
            'NAME',
            '       whoami - print effective user name',
        ],
        theme: [
            'NAME',
            '       theme - change the terminal color scheme',
            '',
            'SYNOPSIS',
            '       theme [name]',
            '',
            'DESCRIPTION',
            '       With no argument, lists available themes.',
            '       Themes: green (default), amber, mono, solarized.',
            '       Selection is persisted in localStorage.',
        ],
        matrix: [
            'NAME',
            '       matrix - wake up neo',
            '',
            'DESCRIPTION',
            '       Fullscreen digital rain. Click or press any key to exit.',
        ],
        snake: [
            'NAME',
            '       snake - play snake',
            '',
            'DESCRIPTION',
            '       Fullscreen overlay snake game.',
            '       Arrow keys / WASD to move. Esc or q to quit.',
            '       After game over, press space to restart.',
        ],
        top: [
            'NAME',
            '       top - display fake processes',
            '',
            'DESCRIPTION',
            '       What\'s really running.',
        ],
        ps: [
            'NAME',
            '       ps - same as top',
        ],
        help: [
            'NAME',
            '       help - show the full command list',
        ],
        man: [
            'NAME',
            '       man - display a manual page',
            '',
            'SYNOPSIS',
            '       man <command>',
        ],
        exit: [
            'NAME',
            '       exit - log out, return to landing',
            '',
            'SYNOPSIS',
            '       exit | logout',
        ],
        sudo: [
            'NAME',
            '       sudo - execute as another user',
            '',
            'DESCRIPTION',
            '       Spoiler: amazingvisitor is not in the sudoers file.',
        ],
    };
    MAN_PAGES.logout = MAN_PAGES.exit;
    MAN_PAGES.spidey = MAN_PAGES.spiderman = ['NAME', '       spiderman - with great power...'];

    // ---------- snake ----------
    let snakeActive = false;
    function runSnake() {
        if (snakeActive) return;
        snakeActive = true;
        const input = $('userInput');
        if (input) input.blur();

        const overlay = document.createElement('div');
        overlay.id = 'snake-overlay';
        Object.assign(overlay.style, {
            position: 'fixed',
            top: '0', right: '0', bottom: '0', left: '0',
            background: '#050507',
            zIndex: '2147483647',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            fontFamily: 'Menlo, monospace',
        });

        const cell = 22;
        const cols = 28, rows = 18;
        const canvas = document.createElement('canvas');
        canvas.width = cols * cell;
        canvas.height = rows * cell;
        canvas.style.background = '#0e0f12';
        canvas.style.border = '1px solid #2a2b30';
        overlay.appendChild(canvas);

        const hud = document.createElement('div');
        hud.style.color = '#02e35c';
        hud.style.marginTop = '0.8em';
        hud.style.fontSize = '0.95em';
        hud.style.letterSpacing = '0.04em';
        overlay.appendChild(hud);

        const hint = document.createElement('div');
        hint.style.color = '#8a8a92';
        hint.style.marginTop = '0.3em';
        hint.style.fontSize = '0.8em';
        hint.textContent = 'arrows / wasd to move · space to restart · q or esc to quit';
        overlay.appendChild(hint);

        document.body.appendChild(overlay);

        const ctx = canvas.getContext('2d');
        let snake, dir, nextDir, food, score, alive, tickInterval;

        function reset() {
            snake = [{ x: Math.floor(cols / 2), y: Math.floor(rows / 2) }];
            dir = { x: 1, y: 0 };
            nextDir = dir;
            food = spawnFood();
            score = 0;
            alive = true;
            updateHud();
        }

        function spawnFood() {
            while (true) {
                const f = { x: Math.floor(Math.random() * cols), y: Math.floor(Math.random() * rows) };
                if (!snake.some(s => s.x === f.x && s.y === f.y)) return f;
            }
        }

        function updateHud() {
            hud.textContent = alive ? `score: ${score}` : `game over · final score: ${score} · press space to play again`;
        }

        function draw() {
            ctx.fillStyle = '#0e0f12';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            // food
            ctx.fillStyle = '#5cccff';
            ctx.fillRect(food.x * cell + 3, food.y * cell + 3, cell - 6, cell - 6);
            // snake
            ctx.fillStyle = '#02e35c';
            for (let i = 0; i < snake.length; i++) {
                const s = snake[i];
                ctx.fillRect(s.x * cell + 1, s.y * cell + 1, cell - 2, cell - 2);
            }
        }

        function tick() {
            if (!alive) return;
            dir = nextDir;
            const head = { x: snake[0].x + dir.x, y: snake[0].y + dir.y };
            if (head.x < 0 || head.x >= cols || head.y < 0 || head.y >= rows
                || snake.some(s => s.x === head.x && s.y === head.y)) {
                alive = false;
                updateHud();
                draw();
                return;
            }
            snake.unshift(head);
            if (head.x === food.x && head.y === food.y) {
                score++;
                food = spawnFood();
                updateHud();
            } else {
                snake.pop();
            }
            draw();
        }

        function onKey(e) {
            const k = e.key;
            if (k === 'Escape' || k === 'q' || k === 'Q') { exit(); return; }
            if ((k === ' ' || k === 'Spacebar') && !alive) { reset(); draw(); return; }
            const map = {
                ArrowUp: { x: 0, y: -1 }, w: { x: 0, y: -1 }, W: { x: 0, y: -1 },
                ArrowDown: { x: 0, y: 1 }, s: { x: 0, y: 1 }, S: { x: 0, y: 1 },
                ArrowLeft: { x: -1, y: 0 }, a: { x: -1, y: 0 }, A: { x: -1, y: 0 },
                ArrowRight: { x: 1, y: 0 }, d: { x: 1, y: 0 }, D: { x: 1, y: 0 },
            };
            const d = map[k];
            if (!d) return;
            // can't reverse onto self
            if (d.x === -dir.x && d.y === -dir.y) return;
            nextDir = d;
            e.preventDefault();
        }

        function exit() {
            clearInterval(tickInterval);
            overlay.remove();
            document.removeEventListener('keydown', onKey);
            snakeActive = false;
            focusInput();
        }

        reset();
        draw();
        tickInterval = setInterval(tick, 110);
        // defer keydown so the Enter that launched snake doesn't get caught
        setTimeout(() => document.addEventListener('keydown', onKey), 0);
    }

    function handleCommand(raw) {
        const trimmed = raw.trim();
        const cmd = trimmed.toLowerCase();
        if (!cmd) {
            // empty Enter: real shells just echo the prompt and move on
            appendBlock(raw, []);
            return;
        }

        history.push(raw);
        historyIdx = history.length;

        // sudo
        if (cmd.startsWith('sudo ')) {
            appendBlock(raw, [`Sorry, ${'amazingvisitor'} is not in the sudoers file. Nice try, though.`]);
            return;
        }

        // echo
        if (cmd.startsWith('echo ')) {
            appendBlock(raw, [trimmed.slice(5)]);
            return;
        }

        // ls [<flags>] [<path>]
        if (cmd === 'ls' || cmd.startsWith('ls ')) {
            const argv = parseArgs(trimmed.slice(2));
            const target = argv.positional.length === 0 ? cwd : resolvePath(argv.positional[0]);
            const node = getNode(target);
            if (!node) {
                appendBlock(raw, [`ls: ${argv.positional[0]}: No such file or directory`]);
                return;
            }
            if (node.type !== 'dir') {
                // ls on a file just prints the file name (real ls behavior)
                appendBlock(raw, [argv.positional[0]]);
                return;
            }
            appendNodes(raw, makeLsNodes(node));
            return;
        }

        // cd [<dir>]
        if (cmd === 'cd' || cmd.startsWith('cd ')) {
            const arg = cmd === 'cd' ? '~' : trimmed.slice(3).trim();
            const target = resolvePath(arg);
            const node = getNode(target);
            if (!node) {
                appendBlock(raw, [`cd: no such file or directory: ${arg}`]);
                return;
            }
            if (node.type !== 'dir') {
                appendBlock(raw, [`cd: not a directory: ${arg}`]);
                return;
            }
            appendBlock(raw, []);
            cwd = target;
            updatePromptPath();
            return;
        }

        // cat <file> [<file>...]
        if (cmd === 'cat' || cmd.startsWith('cat ')) {
            const argRaw = cmd === 'cat' ? '' : trimmed.slice(4).trim();
            if (!argRaw) { appendBlock(raw, []); return; }
            const args = argRaw.split(/\s+/);
            const lines = [];
            let preserveSpaces = false;
            for (const arg of args) {
                const target = resolvePath(arg);
                const node = getNode(target);
                if (!node) { lines.push(`cat: ${arg}: No such file or directory`); continue; }
                if (node.type === 'dir')    { lines.push(`cat: ${arg}: Is a directory`); continue; }
                if (node.type === 'binary') { lines.push(`cat: ${arg}: binary file. use \`open ${arg}\` to download.`); continue; }
                if (node.type === 'link')   { lines.push(`${node.url}`); continue; }
                if (node.type === 'file') {
                    lines.push(...node.content);
                    if (node.preserveSpaces) preserveSpaces = true;
                }
            }
            appendBlock(raw, lines, { preserveSpaces });
            return;
        }

        // open <file>  - opens links/binaries; cd-into for dirs; cat for text files
        if (cmd === 'open' || cmd.startsWith('open ')) {
            const arg = cmd === 'open' ? '' : trimmed.slice(5).trim();
            if (!arg) { appendBlock(raw, ['usage: open <file|link|dir>']); return; }
            const target = resolvePath(arg);
            const node = getNode(target);
            if (!node) { appendBlock(raw, [`open: ${arg}: No such file or directory`]); return; }
            if (node.type === 'dir') { appendBlock(raw, [`open: ${arg}: is a directory; use \`cd ${arg}\``]); return; }
            if (node.type === 'binary' || node.type === 'link') {
                appendBlock(raw, []);
                window.open(node.url, '_blank', 'noopener');
                return;
            }
            if (node.type === 'file') { appendBlock(raw, node.content); return; }
        }

        // man <cmd>
        if (cmd === 'man' || cmd.startsWith('man ')) {
            const arg = cmd === 'man' ? '' : trimmed.slice(4).trim().toLowerCase();
            if (!arg) { appendBlock(raw, ['What manual page do you want? For example, try `man cat`.']); return; }
            const page = MAN_PAGES[arg];
            if (!page) { appendBlock(raw, [`No manual entry for ${arg}`]); return; }
            appendBlock(raw, page, { preserveSpaces: true });
            return;
        }

        // theme [<name>]
        if (cmd === 'theme' || cmd.startsWith('theme ')) {
            const arg = cmd === 'theme' ? '' : trimmed.slice(6).trim().toLowerCase();
            if (!arg) {
                appendBlock(raw, [
                    'available themes (current: ' + currentTheme + '):',
                    '  green       classic green-on-black (default)',
                    '  amber       retro amber phosphor with subtle scanlines',
                    '  mono        monochrome white',
                    '  solarized   solarized light',
                    '',
                    'usage: theme <name>',
                ]);
                return;
            }
            if (!THEMES.includes(arg)) {
                appendBlock(raw, [`theme: unknown theme: ${arg}. try \`theme\` to list.`]);
                return;
            }
            appendBlock(raw, []);
            setTheme(arg);
            return;
        }

        // tree [<dir>]
        if (cmd === 'tree' || cmd.startsWith('tree ')) {
            const argv = parseArgs(trimmed.slice(4));
            const target = argv.positional.length === 0 ? cwd : resolvePath(argv.positional[0]);
            const node = getNode(target);
            if (!node) { appendBlock(raw, [`tree: ${argv.positional[0]}: No such file or directory`]); return; }
            if (node.type !== 'dir') { appendBlock(raw, [argv.positional[0] || pathDisplay(target)]); return; }
            appendNodes(raw, makeTreeNodes(node, pathDisplay(target)));
            return;
        }

        if (cmd in ROUTES) {
            const r = ROUTES[cmd];
            if (r.kind === 'route') window.location.href = r.target;
            else window.open(r.target, '_blank', 'noopener');
            return;
        }

        if (cmd in COMMANDS) {
            const result = COMMANDS[cmd]();
            if (result === '__CLEAR__') {
                clearScreen();
            } else if (result === '__MATRIX__') {
                runMatrix();
            } else if (result === '__EMAIL__') {
                const addr = (window.SITE && window.SITE.email) || 'pratyushsaxena4@gmail.com';
                const p = document.createElement('p');
                p.className = 'computer-text';
                p.innerHTML = `<a href="mailto:${escapeHTML(addr)}">${escapeHTML(addr)}</a>`;
                appendNodes(raw, [p]);
            } else if (result === '__HISTORY__') {
                if (history.length === 0) {
                    appendBlock(raw, []);
                } else {
                    const lines = history.map((h, i) => `${String(i + 1).padStart(5)}  ${h}`);
                    appendBlock(raw, lines, { preserveSpaces: true });
                }
            } else if (result === '__SNAKE__') {
                runSnake();
            } else if (result === '__SPIDERMAN__') {
                const figure = buildPixelArt(SPIDERMAN_PIXELS, PIXEL_PALETTE, PIXEL_SIZE);
                const quote = document.createElement('p');
                quote.className = 'computer-text';
                quote.style.marginTop = '0.6em';
                quote.textContent = '"with great power comes great responsibility." - uncle ben';
                appendNodes(raw, [figure, quote]);
            } else {
                const preserveSpaces = cmd === 'neofetch' || cmd === 'top' || cmd === 'ps';
                appendBlock(raw, result, { preserveSpaces });
            }
            return;
        }

        const firstToken = trimmed.split(/\s+/)[0];
        appendBlock(raw, [`zsh: command not found: ${firstToken}`]);
    }

    function autocomplete(prefix) {
        // path-aware completion for commands that take a file/dir argument
        if (prefix.startsWith('cd '))   return completePath(prefix, 'cd ',   { dirsOnly: true });
        if (prefix.startsWith('cat '))  return completePath(prefix, 'cat ',  { filesOnly: true });
        if (prefix.startsWith('ls '))   return completePath(prefix, 'ls ',   {});
        if (prefix.startsWith('tree ')) return completePath(prefix, 'tree ', { dirsOnly: true });
        if (prefix.startsWith('open ')) return completePath(prefix, 'open ', {});
        if (prefix.startsWith('man '))  return completeCmdName(prefix, 'man ');
        if (prefix.startsWith('theme ')) return completeFromList(prefix, 'theme ', THEMES);

        const all = Object.keys(ROUTES).concat(Object.keys(COMMANDS))
            .concat(['ls', 'cd', 'cat', 'tree', 'open', 'man', 'theme']);
        const matches = all.filter(c => c.startsWith(prefix));
        if (matches.length === 1) return matches[0];
        if (matches.length > 1) {
            const common = longestCommonPrefix(matches);
            appendBlock(prefix, [matches.join('   ')]);
            return common.length > prefix.length ? common : prefix;
        }
        return prefix;
    }

    function completePath(prefix, leader, opts) {
        const arg = prefix.slice(leader.length);
        const lastSlash = arg.lastIndexOf('/');
        const dirPart = lastSlash >= 0 ? arg.slice(0, lastSlash + 1) : '';
        const leafPart = lastSlash >= 0 ? arg.slice(lastSlash + 1) : arg;

        const dirSegments = dirPart ? resolvePath(dirPart) : cwd.slice();
        const node = getNode(dirSegments);
        if (!node || node.type !== 'dir') return prefix;

        let candidates = Object.keys(node.entries).sort();
        if (opts.dirsOnly)  candidates = candidates.filter(n => node.entries[n].type === 'dir');
        if (opts.filesOnly) candidates = candidates.filter(n => node.entries[n].type !== 'dir');

        const matches = candidates.filter(n => n.toLowerCase().startsWith(leafPart.toLowerCase()));
        if (matches.length === 0) return prefix;

        if (matches.length === 1) {
            const m = matches[0];
            const trailing = node.entries[m].type === 'dir' ? '/' : '';
            return leader + dirPart + m + trailing;
        }
        const lower = matches.map(m => m.toLowerCase());
        const commonLower = longestCommonPrefix(lower);
        appendBlock(prefix, [matches.join('   ')]);
        if (commonLower.length > leafPart.length) {
            return leader + dirPart + matches[0].slice(0, commonLower.length);
        }
        return prefix;
    }

    function completeCmdName(prefix, leader) {
        const arg = prefix.slice(leader.length);
        const candidates = Object.keys(MAN_PAGES).sort();
        const matches = candidates.filter(c => c.startsWith(arg));
        if (matches.length === 1) return leader + matches[0];
        if (matches.length > 1) {
            const common = longestCommonPrefix(matches);
            appendBlock(prefix, [matches.join('   ')]);
            return common.length > arg.length ? leader + common : prefix;
        }
        return prefix;
    }

    function completeFromList(prefix, leader, list) {
        const arg = prefix.slice(leader.length);
        const matches = list.filter(c => c.startsWith(arg));
        if (matches.length === 1) return leader + matches[0];
        if (matches.length > 1) {
            const common = longestCommonPrefix(matches);
            appendBlock(prefix, [matches.join('   ')]);
            return common.length > arg.length ? leader + common : prefix;
        }
        return prefix;
    }

    function longestCommonPrefix(strings) {
        if (!strings.length) return '';
        let pref = strings[0];
        for (const s of strings.slice(1)) {
            while (s.indexOf(pref) !== 0) pref = pref.slice(0, -1);
            if (!pref) break;
        }
        return pref;
    }

    window.handleKeyDown = function (event) {
        const input = $('userInput');
        if (!input) return;

        if (event.key === 'Enter') {
            const value = input.value;
            input.value = '';
            handleCommand(value);
            event.preventDefault();
            return;
        }

        if (event.key === 'ArrowUp') {
            if (!history.length) return;
            if (historyIdx === history.length) draft = input.value;
            historyIdx = Math.max(0, historyIdx - 1);
            input.value = history[historyIdx];
            event.preventDefault();
            return;
        }

        if (event.key === 'ArrowDown') {
            if (!history.length) return;
            historyIdx = Math.min(history.length, historyIdx + 1);
            input.value = historyIdx === history.length ? draft : history[historyIdx];
            event.preventDefault();
            return;
        }

        if (event.key === 'Tab') {
            input.value = autocomplete(input.value.toLowerCase());
            event.preventDefault();
            return;
        }

        // Ctrl+L clears (real terminal habit)
        if (event.key === 'l' && event.ctrlKey) {
            clearScreen();
            event.preventDefault();
            return;
        }

        // Ctrl+C cancels the current input. don't override copy when text is selected.
        if (event.key === 'c' && event.ctrlKey) {
            const sel = window.getSelection && window.getSelection().toString();
            if (sel) return;
            appendBlock(input.value + '^C', []);
            input.value = '';
            historyIdx = history.length;
            draft = '';
            event.preventDefault();
            return;
        }
    };

    // ---------- intro renderer ----------
    function buildIntroSteps() {
        return [
            { type: 'boot' },
            { type: 'login' },
            { type: 'cmd', text: 'cat README.md', output: VFS.entries['README.md'].content },
            { type: 'ls' },
        ];
    }

    function makeBootNodes() {
        const lines = [
            'booting pratyush.os v4.0... ok',
            '',
        ];
        return lines.map(l => {
            const p = document.createElement('p');
            p.className = 'computer-text';
            p.textContent = l;
            return p;
        });
    }

    function makeLoginNode() {
        const p = document.createElement('p');
        p.className = 'input-line';
        p.textContent = `Last login: ${lastLoginString()} on ttys003`;
        return p;
    }
    function makePromptNode(text) {
        const p = document.createElement('p');
        p.className = 'input-line';
        p.innerHTML = makePromptHtml() + escapeHTML(text);
        return p;
    }
    function makeOutputNode(line) {
        const p = document.createElement('p');
        p.className = 'computer-text';
        p.textContent = line;
        return p;
    }
    function makeLsNodes(dirNode) {
        const names = Object.keys(dirNode.entries).sort();
        const grid = document.createElement('div');
        grid.className = 'computer-text ls-grid last';
        for (const name of names) {
            const item = dirNode.entries[name];
            const klass = item.type === 'dir' ? 'ls-dir'
                : item.type === 'link' ? 'ls-link'
                : 'ls-file';
            const span = document.createElement('span');
            span.className = klass;
            // dirs get a trailing `/` (mac `ls -F` style); colors do the rest
            span.textContent = item.type === 'dir' ? name + '/' : name;
            grid.appendChild(span);
        }
        return [grid];
    }

    function makeTreeNodes(dirNode, label) {
        const lines = [label || '.'];
        let dirCount = 0, fileCount = 0;
        function walk(node, prefix) {
            const names = Object.keys(node.entries).sort();
            names.forEach((name, i) => {
                const last = i === names.length - 1;
                const branch = last ? '└── ' : '├── ';
                const child = node.entries[name];
                const klass = child.type === 'dir' ? 'ls-dir' : child.type === 'link' ? 'ls-link' : 'ls-file';
                lines.push(prefix + branch + `<span class="${klass}">${escapeHTML(name)}</span>`);
                if (child.type === 'dir') {
                    dirCount++;
                    walk(child, prefix + (last ? '    ' : '│   '));
                } else {
                    fileCount++;
                }
            });
        }
        walk(dirNode, '');
        lines.push('');
        lines.push(`${dirCount} director${dirCount === 1 ? 'y' : 'ies'}, ${fileCount} file${fileCount === 1 ? '' : 's'}`);

        return lines.map(html => {
            const p = document.createElement('p');
            p.className = 'computer-text';
            p.style.whiteSpace = 'pre';
            p.innerHTML = html;
            return p;
        });
    }
    function makeTipNode() {
        const p = document.createElement('p');
        p.className = 'tip';
        p.innerHTML = 'type <code>help</code> any time, or <code>cd about</code> to read more about me.';
        return p;
    }

    function renderIntroStep(container, step) {
        if (step.type === 'boot') {
            for (const node of makeBootNodes()) container.appendChild(node);
            return;
        }
        if (step.type === 'login') return container.appendChild(makeLoginNode());
        if (step.type === 'cmd') {
            container.appendChild(makePromptNode(step.text));
            for (const line of step.output) container.appendChild(makeOutputNode(line));
            return;
        }
        if (step.type === 'ls') {
            container.appendChild(makePromptNode('ls'));
            for (const node of makeLsNodes(VFS)) container.appendChild(node);
            return;
        }
        if (step.type === 'tip') return container.appendChild(makeTipNode());
    }

    function renderIntro() {
        const intro = $('intro');
        if (!intro) return;
        for (const step of buildIntroSteps()) renderIntroStep(intro, step);
    }

    window.addEventListener('DOMContentLoaded', function () {
        const yearEl = $('year');
        if (yearEl) yearEl.textContent = new Date().getFullYear();

        loadTheme();
        renderIntro();
        focusInput();

        // Refocus the input when the user clicks blank space inside the terminal,
        // but never steal focus from links, buttons, or text they're trying to select.
        const term = document.getElementById('terminal');
        if (term) {
            term.addEventListener('click', function (e) {
                if (matrixActive || snakeActive) return;
                if (e.target.closest('a, button, input, textarea, kbd, code')) return;
                const sel = window.getSelection && window.getSelection().toString();
                if (sel) return;
                const i = $('userInput');
                if (i) i.focus({ preventScroll: true });
            });
        }
    });

    window.addEventListener('pageshow', function (event) {
        if (event.persisted) focusInput();
    });
})();
