import * as React from 'react';
import {Dispatch, SetStateAction} from "react";

import {IFailingObjectPage, IValidator} from "../data/interfaces";
import {fetchFailingObjectsForValidator} from "../data/api";
import Spinner from "react-bootstrap/Spinner";
import {FailingObject} from "./failing-object";


interface IFailingObjectList {
    validator_id: number,
    setValidators: Dispatch<SetStateAction<IValidator[]>>
}


export const FailingObjectList: React.FC<IFailingObjectList> = ({
    validator_id,
    setValidators,
}) => {
    const [page, setPage] = React.useState<IFailingObjectPage>({results: [], next: null});
    const [isLoading, setIsLoading] = React.useState(true);

    /* load the initial page on component mount */
    React.useEffect(() => {
        (async function() {
            setIsLoading(true);
            await fetchFailingObjectsForValidator(validator_id, null, setPage);
            setIsLoading(false);
        })();
    }, [validator_id]);

    /* load subsequent-pages */
    const loadNextPage = (event: React.MouseEvent<HTMLDivElement>) => {
        (async function() {
            setIsLoading(true);
            await fetchFailingObjectsForValidator(null, page.next, setPage);
            setIsLoading(false);
        })();
    }

    return (
        <>
        {
            page.results.map(obj =>
                <FailingObject
                    key={obj.id}
                    {...obj}
                    validator_id={validator_id}
                    setValidators={setValidators}
                    setFailingObjectPage={setPage} />
            )
        }
        {isLoading &&
            <div style={{width: "100%"}}>
                 <Spinner animation="border" role="status" variant="primary"
                          style={{margin: "5px 45%"}} />
            </div>
        }
        {(!isLoading) && (page.next !== null) &&
            <div onClick={loadNextPage} style={loadMoreStyle}>
                <div style={{width: "100%", textAlign: "center"}}>Load More...</div>
            </div>
        }
        </>
    );
}


const loadMoreStyle: React.CSSProperties = {
    cursor: "pointer",
    padding: "10px",
    fontWeight: 600,
    fontSize: "10pt",
    background: "#ffe2f673",
    borderBottom: "2px solid #ffade5",
}


export default FailingObjectList;
