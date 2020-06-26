import React from 'react';
import './App.css';

import { ModelStatus } from './components/model-status'
import ModelRow, { ModelRowColgroup } from './components/model-row'


function App() {
  return (
    <table className="summary-table" cellSpacing={0}>
        <ModelRowColgroup />
        <tbody>
          <ModelRow
              appLabel="test_app"
              modelName="TestModel"
              status={ModelStatus.PASSING}
              methods={[]}
          />
          <ModelRow
              appLabel="test_app"
              modelName="TestPage"
              status={ModelStatus.FAILING}
              methods={[]}
          />
      </tbody>
    </table>
  );
}

export default App;
