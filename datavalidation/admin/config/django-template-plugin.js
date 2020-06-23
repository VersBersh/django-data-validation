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

  apply(compiler) {
    compiler.hooks.emit.tap('Django Template Plugin', (compilation) => {
      let index = this.template;

      // grab all assets from the compilation
      let assets = Object
          .keys(compilation.assets)
          .filter(filename => !this.options.excludes.some(excl => filename.match(excl)));

      // inject javascript assets
      let js = assets
          .filter(filename => filename.endsWith(".js"))
          .map(filename => {
            const fullpath = path.join(this.options.staticRoot, filename);
            return `<script src="\{% static "${fullpath}" %\}"></script>`;
          });
      index = index.replace("<:BODY:>", js.join("\n"));

      // inject css assets
      let css = assets
          .filter(filename => filename.endsWith(".css"))
          .map(filename => {
            const fullpath = path.join(this.options.staticRoot, filename);
            return `<link rel="stylesheet" href="\{% static "${fullpath}" %\}" />`
          });
      index = index.replace("<:HEAD:>", css.join("\n"));

      const outputPath = path.join(this.options.outputDir, "index.html");
      fs.writeFileSync(outputPath, index);
    });
  }
}

module.exports = DjangoTempalatePlugin;
