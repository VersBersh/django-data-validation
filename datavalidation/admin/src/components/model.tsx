import * as React from "react";
import {Dispatch, SetStateAction} from "react";
import Accordian from "react-bootstrap/Accordion";

import {Status} from "../data/enums";
import {StatusIndicator} from "./status";
import {fetchTotalObjectCount} from "../data/api";
import {IValidator} from "../data/interfaces";
import {Validator} from "./validator";


export interface IModel {
    appLabel: string,
    modelName: string,
    status: Status,
    validators: IValidator[],
}


interface IModelEx extends IModel {
    setValidators: Dispatch<SetStateAction<IValidator[]>>
}


/**
 * A row for each model displaying the data validation status
 */
export const Model: React.FC<IModelEx> = ({
    appLabel,
    modelName,
    status,
    validators,
    setValidators,
}) => {
    const [totalObjectCount, setTotalObjectCount] = React.useState<number|null>(null);

    React.useEffect(() => {
        fetchTotalObjectCount(appLabel, modelName, setTotalObjectCount).then();
    }, [appLabel, modelName]);

    return (
        <Accordian defaultActiveKey="0" style={{marginBottom: "10px"}}>
            <Accordian.Toggle as="div" eventKey="0" className="vertical-align" style={style}>
                <div className="no-overflow" style={{width: "20%"}} title={modelName}> {modelName} </div>
                <StatusIndicator status={status} onDark={false} />
            </Accordian.Toggle>
            <Accordian.Collapse eventKey="0">
                <div> {
                    Object.values(validators).map(valinfo =>
                        <Validator
                            key={`${appLabel}.${modelName}.${valinfo.method_name}`}
                            totalObjectCount={totalObjectCount}
                            {...valinfo}
                            setValidators={setValidators}
                        />
                    )
                } </div>
            </Accordian.Collapse>
        </Accordian>
    )
}


const style: React.CSSProperties = {
    cursor: "pointer",
    padding: "10px",
    background: "#ebebeb",
    fontWeight: 600,
    fontSize: "14pt",
    color: "#000",
};


export default Model;