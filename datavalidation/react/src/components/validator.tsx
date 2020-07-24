import * as React from "react";
import Accordian from "react-bootstrap/Accordion";
import Spinner from "react-bootstrap/Spinner"
import SyntaxHighlighter from "react-syntax-highlighter";
import {docco} from "react-syntax-highlighter/dist/esm/styles/hljs";

import {Status} from "../data/enums";
import {IValidator} from "../data/interfaces";
import {StatusIcon, getStatusColour} from "./status";
import {parseDate, formatDate, formatSeconds} from "../utils";
import {FailingObjectList} from "./failing-object-list";
import {Dispatch, SetStateAction} from "react";


interface IValidatorEx extends IValidator {
    totalObjectCount: number | null,
    setValidators: Dispatch<SetStateAction<IValidator[]>>
}


export const Validator: React.FC<IValidatorEx> = ({
    id,
    method_name,
    description,
    last_run_time,
    execution_time,
    status,
    num_passing,
    num_failing,
    num_na,
    num_allowed_to_fail,
    exc_type,
    exc_traceback,
    exc_obj_pk,
    totalObjectCount,
    setValidators,
}) => {
    const isException = exc_type !== null;

    const all_null = (num_passing === null) && (num_failing === null) && (num_na === null);
    if (all_null) {
        num_allowed_to_fail = null;
    }

    const totalValidated = (num_passing !== null) && (num_failing !== null) && (num_na !== null)
        ? num_passing + num_failing + num_na
        : null;

    const totalUnvalidated = (totalObjectCount !== null) && (totalValidated !== null)
        ? totalObjectCount - totalValidated
        : null;

    const last_run_time_fmt = last_run_time
        ? formatDate(parseDate(last_run_time), "%Y-%m-%d %H:%M:%S")
        : "N/A";

    const cursor = exc_traceback || ((num_failing || 0) > 0) ? "pointer" : "default"

    return (
        <Accordian defaultActiveKey="" style={{marginBottom: "10px"}}>
            <Accordian.Toggle as="div" eventKey="0" className="vertical-align" style={{cursor, ...style}}>
                <table style={{width: "100%", tableLayout: "fixed"}}>
                <tbody>
                    <tr style={{verticalAlign: "middle", fontSize: "11pt", fontWeight: 600}}>
                        <td className="no-overflow" style={wide} title={method_name}> {method_name} </td>
                        <td rowSpan={2} style={{width: "5%"}}> <StatusIcon status={status} onDark={false} /> </td>
                        <td style={{fontSize: "10pt", fontWeight: "normal", ...col2}}> {last_run_time_fmt} </td>
                        <td style={{fontSize: "10pt", fontWeight: "normal", ...thin}}> {formatSeconds(execution_time)} </td>
                        {!isException &&
                        <>
                            <td style={thin}>{num_passing}</td>
                            <td style={thin}>{num_failing}</td>
                            <td style={thin}>{num_na}</td>
                            <td style={thin}>{num_allowed_to_fail}</td>
                            <td style={thin}>
                                {
                                    totalObjectCount === undefined
                                       ? <Spinner animation="border" role="status" variant="primary" />
                                       : totalUnvalidated
                                }
                            </td>
                        </>
                        }
                        {isException &&
                            <td rowSpan={2} style={{width: "50%", color: getStatusColour(Status.EXCEPTION)}}>
                                {exc_type}
                                {exc_obj_pk === null ? "" : ` at object id: ${exc_obj_pk}`}
                            </td>
                        }
                        <td> </td>
                    </tr>

                    <tr className="small-text" style={{verticalAlign: "top"}}>
                        <td style={wide}>{description}</td>
                        <td style={col2}>last run time</td>
                        <td style={thin}>execution time (s)</td>
                        {!isException &&
                        <>
                            <td style={thin}>passing</td>
                            <td style={thin}>failing</td>
                            <td style={thin}>N/A</td>
                            <td style={thin}>allowed to fail</td>
                            <td style={thin}>unvalidated</td>
                        </>
                        }
                        <td>{/* to fill remaining column space */}</td>
                    </tr>
                </tbody>
                </table>
            </Accordian.Toggle>

            <Accordian.Collapse eventKey="0">
                <>
                {exc_traceback &&
                    <SyntaxHighlighter language="python" style={docco}>
                         {exc_traceback}
                    </SyntaxHighlighter>
                }
                {(!isException) && ((num_failing || 0) > 0) &&
                    <FailingObjectList validator_id={id} setValidators={setValidators} />
                }
                </>
            </Accordian.Collapse>
        </Accordian>
    )
}


const style: React.CSSProperties = {
    padding: "10px 0",
    background: "#fff",
    fontWeight: 500,
    fontSize: "14pt",
    color: "#000",
    borderBottom: "1px solid #ebebeb",
};


const wide: React.CSSProperties = {
    width: "20%",
}

const col2: React.CSSProperties = {
    width: "10%",
}

const thin: React.CSSProperties = {
    width: "10%",
}


export default Validator;