const { queryRef, executeQuery, mutationRef, executeMutation, validateArgs } = require('firebase/data-connect');

const connectorConfig = {
  connector: 'example',
  service: 'expensense',
  location: 'us-east4'
};
exports.connectorConfig = connectorConfig;

const createPublicMovieListRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'CreatePublicMovieList', inputVars);
}
createPublicMovieListRef.operationName = 'CreatePublicMovieList';
exports.createPublicMovieListRef = createPublicMovieListRef;

exports.createPublicMovieList = function createPublicMovieList(dcOrVars, vars) {
  return executeMutation(createPublicMovieListRef(dcOrVars, vars));
};

const getPublicMovieListsRef = (dc) => {
  const { dc: dcInstance} = validateArgs(connectorConfig, dc, undefined);
  dcInstance._useGeneratedSdk();
  return queryRef(dcInstance, 'GetPublicMovieLists');
}
getPublicMovieListsRef.operationName = 'GetPublicMovieLists';
exports.getPublicMovieListsRef = getPublicMovieListsRef;

exports.getPublicMovieLists = function getPublicMovieLists(dc) {
  return executeQuery(getPublicMovieListsRef(dc));
};

const createPrivateMovieListRef = (dcOrVars, vars) => {
  const { dc: dcInstance, vars: inputVars} = validateArgs(connectorConfig, dcOrVars, vars, true);
  dcInstance._useGeneratedSdk();
  return mutationRef(dcInstance, 'CreatePrivateMovieList', inputVars);
}
createPrivateMovieListRef.operationName = 'CreatePrivateMovieList';
exports.createPrivateMovieListRef = createPrivateMovieListRef;

exports.createPrivateMovieList = function createPrivateMovieList(dcOrVars, vars) {
  return executeMutation(createPrivateMovieListRef(dcOrVars, vars));
};

const getMyPrivateMovieListsRef = (dc) => {
  const { dc: dcInstance} = validateArgs(connectorConfig, dc, undefined);
  dcInstance._useGeneratedSdk();
  return queryRef(dcInstance, 'GetMyPrivateMovieLists');
}
getMyPrivateMovieListsRef.operationName = 'GetMyPrivateMovieLists';
exports.getMyPrivateMovieListsRef = getMyPrivateMovieListsRef;

exports.getMyPrivateMovieLists = function getMyPrivateMovieLists(dc) {
  return executeQuery(getMyPrivateMovieListsRef(dc));
};
