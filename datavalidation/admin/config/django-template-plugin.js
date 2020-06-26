const fs = require('fs');
const path = require('path');
const validateOptions = require('schema-utils');


const options_schema = {
  type: 'object',
  properties: {
    // the static directory in the django app (i.e. static/<app_name>)
    staticRoot: {
      type: 'string',
    },
    // the path to the meta django template
    templatePath: {
      type: 'string',
    },
    // the directory to write index.html (i.e. templates/<app_name>)
    outputDir: {
      type: 'string',
    },
    // a list of regex that match any assets to be excluded from index.html
    excludes: {
      type: 'array',
    }
  },
  additionalProperties: false,
  required: ['staticRoot', 'templatePath', 'outputDir'],
};


/**
 *  Create a Django Template (index.html) to return from the admin view
 *
 *  It processes a simple meta template which,
 *  replaces the string <:HEAD:> with <link> elements to all css assets
 *  replaces the string <:BODY:> with <script> elements to all js assets
 */
class DjangoTempalatePlugin {

  constructor(options = {}){
    validateOptions(options_schema, options, 'DjangoTemplatePlugin');
    this.options = {excludes: [], ...options};
    // staticRoot will start with /static directory, but this is implicit in django
    // templates when using the {% static ... %} tag, so we strip it off.
    console.assert(options.staticRoot.startsWith("/static"));
    this.options.staticRoot = options.staticRoot.replace(/^\/static/, '');
    this.template = fs.readFileSync(options.templatePath, {encoding: "utf8"});
  }

  toHTML = (assets, extension, tag, link, attrs = {}) => {
    return assets
          .filter(filename => filename.endsWith(extension))
          .map(filename => {
            const fullpath = path.join(this.options.staticRoot, filename);
            const attr_str = Object.entries(attrs).map(([key, val]) => `${key}="${val}"`).join(" ");
            const link_str = `${link}="\{% static "${fullpath}" %\}"`
            return `<${tag} ${attr_str} ${link_str}> </${tag}>`;
          });
  }

  apply = (compiler) => {
    compiler.hooks.emit.tap('Django Template Plugin', (compilation) => {
      let index = this.template;

      // replace <:STATIC_ROOT:>
      index = index.replace(/<:STATIC_ROOT:>/g, this.options.staticRoot);

      // grab all assets from the compilation
      let assets = Object
          .keys(compilation.assets)
          .filter(filename => !this.options.excludes.some(excl => filename.match(excl)));

      // inject javascript assets into body
      let js = this.toHTML(assets, ".js", "script", "src")
      index = index.replace("<:BODY:>", js.join("\n"));
      console.log("compiling django template")
      console.log(js)

      // inject css assets into head
      let css = this.toHTML(
          assets, ".css", "link", "href", {rel: "stylesheet"}
          );
      index = index.replace("<:HEAD:>", css.join("\n"));

      const outputPath = path.join(this.options.outputDir, "index.html");
      fs.writeFileSync(outputPath, index);
    });
  }
}

module.exports = DjangoTempalatePlugin;
