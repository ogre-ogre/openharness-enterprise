// Test pptxgenjs
var PptxGenJS = require('/home/ai-app/.oh-enterprise/node_modules/pptxgenjs/dist/pptxgenjs.cjs.js');
var pptx = new PptxGenJS();
pptx.addSlide().addText('Test Slide', {x: 1, y: 1});
pptx.save('/home/ai-app/.oh-enterprise/users/3/downloads/test.pptx');
console.log('PPTX file created successfully');