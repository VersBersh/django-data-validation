import {Dispatch, SetStateAction} from 'react';
import axios, {AxiosResponse} from "axios";

import {urlJoin} from "../utils";
import {IFailingObject, IFailingObjectPage, IValidator} from "./interfaces";
import * as FailingObjectSchema from "./schemas/failing-objects";
import * as ValidatorSchema from "./schemas/validator";


const API = urlJoin(window.location.href, "/api/");


/**
 * fetch the name of the CSRF header and cookie for the particular
 * django project
 *
 * If the django project enables CSRF (which it does by default) then
 * the csrf token is required to make requests
 */
export async function fetchCSRFInfo() {
    try {
        const response = await axios.get(urlJoin(API, "meta/csrf/"));
        axios.defaults.xsrfHeaderName = response.data.csrf_header_name;
        axios.defaults.xsrfCookieName = response.data.csrf_cookie_name;
    } catch (e) {
        console.error("[fetchCSRFInfo]", e);
    }
}


/**
 * fetch the total number of objects for a given django model.
 *
 * Counting the total number of records in a database table typically
 * requires a sequential scan, which can be quite slow. Therefore we
 * fetch this via ajax for each individual model. If one table is too
 * large/slow to count then this will hit a timeout exception and we
 * only miss that piece of data.
 */
export async function fetchTotalObjectCount(
    appLabel: string, modelName: string,
    setState: Dispatch<SetStateAction<number|null>>
) {
    try {
        const response = await axios.get(
            urlJoin(API, "meta/object-counts/"),
            {params: {appLabel, modelName}}
        );
        setState(response.data);
    } catch (e) {
        console.error("[fetchTotalObjectCount]", e);
    }
}


/**
 * fetch the list of Validators
 */
export async function fetchValidators(
    setState: Dispatch<SetStateAction<IValidator[]>>
) {
    try {
        const response = await axios.get(urlJoin(API, "validator-summary/"));
        setState(ValidatorSchema.fromJSON(response.data));
    } catch (e) {
        console.error("[fetchValidators]", e);
    }
}


/**
 * patch a Validator
 */
export async function patchValidator(obj: IValidator) {
    try {
        await axios.put(
            urlJoin(API, `validator-summary/${obj.id}/`), obj
        );
    } catch (e) {
        console.error("[patchValidator]", e);
    }
}


/**
 * fetch the list of FailingObjects for a given Validator.
 *
 * /api/failing-objects/ returns paginated results. To get the next
 * page of results this method is called with validator_id=null, and
 * next=the url that was returned by the endpoint on the previous call
 */
export async function fetchFailingObjectsForValidator(
    validator_id: number | null,
    next: string | null,
    setState: Dispatch<SetStateAction<IFailingObjectPage>>
) {
    try {
        let response: AxiosResponse;
        if (validator_id !== null) {
            const url = urlJoin(API, "failing-objects/")
            response = await axios.get(url, {params: {validator_id}});
        } else if (next !== null) {
            response = await axios.get(next);
        } else {
            console.error("validator_id and next cannot both be null!");
            return;
        }
        // don't replace the state, add the next page of results
        const data = FailingObjectSchema.fromJSON(response.data);
        setState(prevState => ({
            results: [...prevState.results, ...data.results],
            next: data.next
        }));
    } catch (e) {
        console.error("[fetchFailingObjectsForValidator]", e);
    }
}


/**
 * patch a FailingObject
 */
export async function patchFailingObject(obj: IFailingObject) {
    try {
        await axios.put(
            urlJoin(API, `failing-objects/${obj.id}/`), obj
        );
    } catch (e) {
        console.error("[patchFailingObject]", e);
    }
}



