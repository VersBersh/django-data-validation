import * as React from 'react';
import {Dispatch, FormEvent, SetStateAction} from "react";

import {IFailingObject, IFailingObjectPage, IValidator} from "../data/interfaces";
import {patchFailingObject, patchValidator} from "../data/api"
import {Status} from "../data/enums";


/**
 * update the component state and patch changes to the REST API
 */
function updateFailingObject(
    id: number, property: string, value: any,
    setPage: Dispatch<SetStateAction<IFailingObjectPage>>,
    patch: boolean = true
) {
    setPage(prevState => ({
        next: prevState.next,
        results: prevState.results.map(failingObj => {
            if (failingObj.id === id) {
                const obj = {...failingObj, [property]: value} as IFailingObject;
                patch && patchFailingObject(obj).catch(console.error);
                return obj;
            }
            return failingObj;
        })
    }));
}


/**
 * handle the state change when the "allowed to fail" box is changed
 *
 * If the number allowed to fail is equal to the number failing then
 * the Status must be updated to PASSING and vice versa.
 */
function updateAllowedToFail(
    id: number,
    validator_id: number,
    allowed_to_fail: boolean,
    setPage: Dispatch<SetStateAction<IFailingObjectPage>>,
    setValidators: Dispatch<SetStateAction<IValidator[]>>,
) {
    updateFailingObject(id, "allowed_to_fail", allowed_to_fail, setPage);
    setValidators(prevState => {
        return prevState.map(validator => {
            if (
                validator.id !== validator_id ||
                validator.num_allowed_to_fail === null ||
                validator.num_failing === null
            ) {
                return validator;
            }

            const new_validator = {...validator};
            if (allowed_to_fail) {
                // @ts-ignore: possibly null
                new_validator.num_allowed_to_fail += 1;
                if (new_validator.num_failing === new_validator.num_allowed_to_fail) {
                    new_validator.status = Status.PASSING;
                    patchValidator(new_validator).catch(console.error);
                }
            } else {
                // @ts-ignore: possibly null
                new_validator.num_allowed_to_fail -= 1;
                // @ts-ignore: possibly null
                if (new_validator.num_failing === new_validator.num_allowed_to_fail + 1) {
                    new_validator.status = Status.FAILING;
                    patchValidator(new_validator).catch(console.error);
                }
            }
            return new_validator;
        })
    });
}


interface IFailingObjectEx extends IFailingObject {
    validator_id: number,
    setValidators: Dispatch<SetStateAction<IValidator[]>>
    setFailingObjectPage: Dispatch<SetStateAction<IFailingObjectPage>>
}

export const FailingObject: React.FC<IFailingObjectEx> = ({
    id,
    object_pk,
    comment,
    admin_page,
    allowed_to_fail,
    allowed_to_fail_justification,
    validator_id,
    setValidators,
    setFailingObjectPage,
}) => {
    const handleCheckboxChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        updateAllowedToFail(
            id, validator_id, event.target.checked,
            setFailingObjectPage, setValidators
        )
    };

    const [prevText, setPrevText] = React.useState<string|null>(null);
    const textBox = React.useRef<HTMLDivElement|null>(null);

    // patch changes to the REST API
    const handleTextBoxChange = async (event: FormEvent<HTMLDivElement>) => {
        const target = event.target as HTMLDivElement;
        const text = target.textContent;
        if (text !== prevText) {
            setPrevText(text);
            // wait 1 seconds for more changes before updating the object
            // don't update state because that causes the component to
            // rerender and the cursor to be reset at the beginning
            setTimeout(() => {
                const currText = textBox.current?.textContent;
                if (currText === text) {
                    patchFailingObject({
                        id,
                        "validator": validator_id,
                        object_pk,
                        comment,
                        allowed_to_fail,
                        "allowed_to_fail_justification": text,
                    } as IFailingObject).catch(console.error);
                }
            }, 1000);
        }
    };

    // update the state on Blur
    const handleTextBoxBlur = (event: React.FocusEvent<HTMLInputElement>) => {
        const target = event.target as HTMLDivElement;
        const text = target.textContent;
        updateFailingObject(id, "allowed_to_fail_justification",
                            text, setFailingObjectPage, false);
    }

    return (
        <div style={{padding: "5px 10px", background: "#ffe2f673", borderBottom: "1px solid #ffade5"}}>
            <table style={{width: "100%"}}>
            <tbody>
                <tr style={{verticalAlign: "middle", fontSize: "10pt", fontWeight: 600, maxHeight: "25px"}}>
                    <td style={{padding: "0 10px", ...thin}}>{object_pk}</td>
                    <td rowSpan={2} style={thin}>
                        {admin_page
                          ? <a href={admin_page} target="_blank" rel="noopener noreferrer">admin page</a>
                          : "admin_page"}
                    </td>
                    <td style={{width: "20%", color: "#8e0000", fontWeight: 500, fontStyle: "italic"}}>
                        {comment}
                    </td>
                    <td style={thin}>
                        <input type="checkbox"
                               defaultChecked={allowed_to_fail}
                               onChange={handleCheckboxChange}/>
                    </td>
                    <td rowSpan={3}>
                        <div className="textarea-div"
                             contentEditable="true"
                             placeholder="justification if allowed to fail"
                             ref={textBox}
                             onInput={handleTextBoxChange}
                             onBlur={handleTextBoxBlur}
                            suppressContentEditableWarning={true}>
                            {allowed_to_fail_justification}
                        </div>
                    </td>
                </tr>

                <tr className="small-text" style={{verticalAlign: "top", maxHeight: "25px"}}>
                    <td style={thin}>object id</td>
                    <td style={thin}>comment</td>
                    <td style={thin}>allowed to fail</td>
                </tr>

                <tr style={{height: "100%"}}>{/* to expand with text area */}</tr>
            </tbody>
            </table>
        </div>
    );
}


const thin: React.CSSProperties = {
    width: "10%",
}


export default FailingObject;
