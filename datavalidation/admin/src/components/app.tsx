import * as React from "react";
import {Dispatch, SetStateAction} from "react";
import Accordian from "react-bootstrap/Accordion";

import {Status} from "../data/enums";
import {StatusIndicator} from "./status";
import {IValidator} from "../data/interfaces";
import {Model, IModel} from "./model";


export interface IApp {
    appLabel: string,
    status: Status,
    models: {
        [modelName: string]: IModel,
    }
}


interface IAppEx extends IApp {
    setValidators: Dispatch<SetStateAction<IValidator[]>>
}


export const App: React.FC<IAppEx> = ({
    appLabel,
    status,
    models,
    setValidators,
}) => {
    return (
        <Accordian defaultActiveKey="0" style={{minWidth: "1000px", marginBottom: "10px"}}>
            <Accordian.Toggle as="div" eventKey="0" className="vertical-align" style={style}>
                <div className="no-overflow" style={{width: "20%"}} title={appLabel}> {appLabel} </div>
                <StatusIndicator status={status} onDark={true} />
            </Accordian.Toggle>
            <Accordian.Collapse eventKey="0">
                <div> {
                    Object.entries(models).map(([modelName, info]) =>
                        <Model
                            key={`${appLabel}.${modelName}`}
                            appLabel={appLabel}
                            modelName={modelName}
                            status={info.status}
                            validators={info.validators}
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
    background: "#417690",
    fontWeight: 600,
    fontSize: "14pt",
    color: "white",
};


export default App;