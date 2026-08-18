// ============ MARKDOWN CONFIGURATION ============
let markdownConfig = {
    gfm: true,
    breaks: true,
    headerIds: false,
    mangle: false,
    highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) {
            try {
                return hljs.highlight(code, { language: lang }).value;
            } catch (e) {
                return code;
            }
        }
        try {
            return hljs.highlightAuto(code).value;
        } catch (e) {
            return code;
        }
    }
};

if (typeof marked !== 'undefined') {
    marked.setOptions(markdownConfig);
    console.log('✅ Markdown configured for streaming');
}

// ... Copying existing functions (FETCH_HELPER to sendChatMessageStream) ...
