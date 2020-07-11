import React from 'react';
import ReactDOM from 'react-dom';
import 'bootstrap/dist/css/bootstrap.min.css';

import './index.css';
import AppList from './components/app-list';


ReactDOM.render(
  <React.StrictMode>
    <AppList />
  </React.StrictMode>,
  document.getElementById('root')
);
