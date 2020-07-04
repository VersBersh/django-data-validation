import Ajv from "ajv";
import {IValidator} from "../interfaces";

import {
    bool, integer, string, optional_integer, optional_string,
    ValidationError,
} from "./utils";


const schema = {
    "type": "array",
    "items": {
        "$ref": "#/definitions/validationSummary"
    },
    "definitions": {
        "validationSummary": {
            "type": "object",
            "properties": {
                "id": integer,
                "app_label": string,
                "model_name": string,
                "method_name": string,
                "description": string,
                "is_class_method": bool,
                "last_run_time": optional_string,
                "status": integer,
                "num_passing": optional_integer,
                "num_failing": optional_integer,
                "num_na": optional_integer,
                "num_allowed_to_fail": optional_integer,
                "exc_type": optional_string,
                "exc_traceback": optional_string,
                "exc_obj_pk": optional_integer,
            },
            "additionalProperties": false,
            "required": [] as string[],
        },
    }
}
schema.definitions.validationSummary.required =
    Object.keys(schema.definitions.validationSummary.properties);

const ajv = new Ajv().compile(schema);

export function validate(data: any): data is IValidator[] {
    return ajv(data) as boolean;
}

export function fromJSON(data: any): IValidator[] {
    if (validate(data)) {
        return data;
    } else {
        throw new ValidationError(`invalid data: ${JSON.stringify(ajv.errors)}`);
    }
}
