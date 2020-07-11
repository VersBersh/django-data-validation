import Ajv from "ajv";
import {IFailingObjectPage} from "../interfaces";

import {
    bool, integer, string, optional_string, ValidationError
} from "./utils";


const schema = {
    "type": "object",
    "properties": {
        "next": optional_string,
        "results": {
            "type": "array",
            "items": {
                "$ref": "#/definitions/failingObject",
            },
        }
    },
    "additionalProperties": true,
    "required": ["next", "results"],
    "definitions": {
        "failingObject": {
            "type": "object",
            "properties": {
                "id": integer,
                "validator": integer,
                "object_pk": integer,
                "allowed_to_fail": bool,
                "allowed_to_fail_justification": string,
                "comment": string,
                "admin_page": string,
            },
            "additionalProperties": false,
            "required": [] as string[],
        }
    }
}
schema.definitions.failingObject.required =
    Object.keys(schema.definitions.failingObject.properties);

const ajv = new Ajv().compile(schema)

export function validate(data: any): data is IFailingObjectPage {
    return ajv(data) as boolean;
}

export function fromJSON(data: any): IFailingObjectPage {
    if (validate(data)) {
        return data;
    } else {
        throw new ValidationError(`invalid data: ${JSON.stringify(ajv.errors)}`)
    }
}