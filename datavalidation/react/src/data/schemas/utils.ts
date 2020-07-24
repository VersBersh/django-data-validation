export const bool = {"type": "boolean"};
export const integer = {"type": "integer"};
export const optional_integer = {"type": ["integer", "null"]};
export const string = {"type": "string"};
export const optional_string = {"type": ["string", "null"]};
export const optional_number = {"type": ["number", "null"]};

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

export type ValiationResult<T> = T | Error;

