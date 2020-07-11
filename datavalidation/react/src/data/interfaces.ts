import {Status} from "./enums";


/** interface to Django model Validator */
export interface IValidator {
    id: number,
    app_label: string,
    model_name: string,
    method_name: string,
    description: string,
    is_class_method: boolean,
    last_run_time: string | null,
    status: Status,
    num_passing: number | null,
    num_failing: number | null,
    num_na: number | null,
    num_allowed_to_fail: number | null,
    exc_type: string | null,
    exc_traceback: string | null,
    exc_obj_pk: number | null,
}


/** interface to Django model FailingObject */
export interface IFailingObject {
    id: number,
    validator: number,
    object_pk: number,
    comment: string,
    allowed_to_fail: boolean,
    allowed_to_fail_justification: string,
    admin_page: string,
}


/** interface to REST API response data */
export interface IFailingObjectPage {
    results: IFailingObject[],
    next: string | null,  // url to the next page of results
}