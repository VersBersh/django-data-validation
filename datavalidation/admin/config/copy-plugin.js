const fs = require('fs-extra');
const validateOptions = require('schema-utils');


const options_schema = {
  type: 'object',
  properties: {
    // the source directory to copy
    src: {
      type: 'string',
    },
    // the destination directory to copy
    dest: {
      type: 'string',
    },
    // an array of regex to exclude
    excludes: {
      type: 'array',
    },
  },
  additionalProperties: false,
  required: ['src', 'dest'],
};


/**
 *  Copy a src folder to a destination
 */
class CopyPlugin {

  constructor(options = {}){
    validateOptions(options_schema, options, 'DjangoTemplatePlugin');
    this.options = {excludes: [], ...options};
  }

  apply = (compiler) => {
    compiler.hooks.emit.tap('Django Template Plugin', _ => {
      fs.copySync(this.options.src, this.options.dest, {
        dereference: true,
        filter: filename => !this.options.excludes.some(excl => filename.match(excl)),
      });
    });
  }
}

module.exports = CopyPlugin;
