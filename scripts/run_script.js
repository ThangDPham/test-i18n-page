const fs = require('fs-extra');
const path = require('path');
const { JSDOM } = require('jsdom');
const { applyTranslation, supportedLanguages } = require('./translate.js');
require('dotenv').config(); // Add this line to load .env file

(async () => {
    try {
        const baseDir = path.resolve(__dirname, '..');
        const englishHtmlPath = path.join(baseDir, 'original', 'index.html');

        if (!(await fs.pathExists(englishHtmlPath))) {
            throw new Error(`English HTML file not found: ${englishHtmlPath}`);
        }

        const html = await fs.readFile(englishHtmlPath, 'utf8');

        // Load baseUrl from .env file
        const baseUrl = process.env.BASE_URL;
        const usePathParam = true;

        for (const lang of supportedLanguages) {
            console.log(`Processing ${lang.text} (${lang.value})...`);

            const dom = new JSDOM(html);
            await applyTranslation(dom.window.document, lang.value, {
                baseUrl,
                usePathParam,
                currentPath: `${lang.value}/`
            });

            const modifiedHtml = dom.serialize();

            const outputPath = path.join(baseDir, lang.value, 'index.html');
            await fs.outputFile(outputPath, modifiedHtml, 'utf8');
            console.log(`Translated HTML saved to ${outputPath}`);
        }

        console.log('All processing completed successfully.');
    } catch (error) {
        console.error('Error during processing:', error);
    }
})();