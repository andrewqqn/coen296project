import { ConnectorConfig, DataConnect, QueryRef, QueryPromise, MutationRef, MutationPromise } from 'firebase/data-connect';

export const connectorConfig: ConnectorConfig;

export type TimestampString = string;
export type UUIDString = string;
export type Int64String = string;
export type DateString = string;




export interface CreatePrivateMovieListData {
  movieList_insert: MovieList_Key;
}

export interface CreatePrivateMovieListVariables {
  name: string;
  description: string;
}

export interface CreatePublicMovieListData {
  movieList_insert: MovieList_Key;
}

export interface CreatePublicMovieListVariables {
  name: string;
  description: string;
}

export interface GetMyPrivateMovieListsData {
  movieLists: ({
    id: UUIDString;
    name: string;
    description?: string | null;
    createdAt: TimestampString;
    updatedAt: TimestampString;
  } & MovieList_Key)[];
}

export interface GetPublicMovieListsData {
  movieLists: ({
    id: UUIDString;
    name: string;
    description?: string | null;
    createdAt: TimestampString;
    updatedAt: TimestampString;
  } & MovieList_Key)[];
}

export interface MovieListItem_Key {
  movieListId: UUIDString;
  position: number;
  __typename?: 'MovieListItem_Key';
}

export interface MovieList_Key {
  id: UUIDString;
  __typename?: 'MovieList_Key';
}

export interface Movie_Key {
  id: UUIDString;
  __typename?: 'Movie_Key';
}

export interface Review_Key {
  id: UUIDString;
  __typename?: 'Review_Key';
}

export interface User_Key {
  id: UUIDString;
  __typename?: 'User_Key';
}

export interface Watch_Key {
  id: UUIDString;
  __typename?: 'Watch_Key';
}

interface CreatePublicMovieListRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreatePublicMovieListVariables): MutationRef<CreatePublicMovieListData, CreatePublicMovieListVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: CreatePublicMovieListVariables): MutationRef<CreatePublicMovieListData, CreatePublicMovieListVariables>;
  operationName: string;
}
export const createPublicMovieListRef: CreatePublicMovieListRef;

export function createPublicMovieList(vars: CreatePublicMovieListVariables): MutationPromise<CreatePublicMovieListData, CreatePublicMovieListVariables>;
export function createPublicMovieList(dc: DataConnect, vars: CreatePublicMovieListVariables): MutationPromise<CreatePublicMovieListData, CreatePublicMovieListVariables>;

interface GetPublicMovieListsRef {
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetPublicMovieListsData, undefined>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect): QueryRef<GetPublicMovieListsData, undefined>;
  operationName: string;
}
export const getPublicMovieListsRef: GetPublicMovieListsRef;

export function getPublicMovieLists(): QueryPromise<GetPublicMovieListsData, undefined>;
export function getPublicMovieLists(dc: DataConnect): QueryPromise<GetPublicMovieListsData, undefined>;

interface CreatePrivateMovieListRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreatePrivateMovieListVariables): MutationRef<CreatePrivateMovieListData, CreatePrivateMovieListVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: CreatePrivateMovieListVariables): MutationRef<CreatePrivateMovieListData, CreatePrivateMovieListVariables>;
  operationName: string;
}
export const createPrivateMovieListRef: CreatePrivateMovieListRef;

export function createPrivateMovieList(vars: CreatePrivateMovieListVariables): MutationPromise<CreatePrivateMovieListData, CreatePrivateMovieListVariables>;
export function createPrivateMovieList(dc: DataConnect, vars: CreatePrivateMovieListVariables): MutationPromise<CreatePrivateMovieListData, CreatePrivateMovieListVariables>;

interface GetMyPrivateMovieListsRef {
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetMyPrivateMovieListsData, undefined>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect): QueryRef<GetMyPrivateMovieListsData, undefined>;
  operationName: string;
}
export const getMyPrivateMovieListsRef: GetMyPrivateMovieListsRef;

export function getMyPrivateMovieLists(): QueryPromise<GetMyPrivateMovieListsData, undefined>;
export function getMyPrivateMovieLists(dc: DataConnect): QueryPromise<GetMyPrivateMovieListsData, undefined>;

