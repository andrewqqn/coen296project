import { CreatePublicMovieListData, CreatePublicMovieListVariables, GetPublicMovieListsData, CreatePrivateMovieListData, CreatePrivateMovieListVariables, GetMyPrivateMovieListsData } from '../';
import { UseDataConnectQueryResult, useDataConnectQueryOptions, UseDataConnectMutationResult, useDataConnectMutationOptions} from '@tanstack-query-firebase/react/data-connect';
import { UseQueryResult, UseMutationResult} from '@tanstack/react-query';
import { DataConnect } from 'firebase/data-connect';
import { FirebaseError } from 'firebase/app';


export function useCreatePublicMovieList(options?: useDataConnectMutationOptions<CreatePublicMovieListData, FirebaseError, CreatePublicMovieListVariables>): UseDataConnectMutationResult<CreatePublicMovieListData, CreatePublicMovieListVariables>;
export function useCreatePublicMovieList(dc: DataConnect, options?: useDataConnectMutationOptions<CreatePublicMovieListData, FirebaseError, CreatePublicMovieListVariables>): UseDataConnectMutationResult<CreatePublicMovieListData, CreatePublicMovieListVariables>;

export function useGetPublicMovieLists(options?: useDataConnectQueryOptions<GetPublicMovieListsData>): UseDataConnectQueryResult<GetPublicMovieListsData, undefined>;
export function useGetPublicMovieLists(dc: DataConnect, options?: useDataConnectQueryOptions<GetPublicMovieListsData>): UseDataConnectQueryResult<GetPublicMovieListsData, undefined>;

export function useCreatePrivateMovieList(options?: useDataConnectMutationOptions<CreatePrivateMovieListData, FirebaseError, CreatePrivateMovieListVariables>): UseDataConnectMutationResult<CreatePrivateMovieListData, CreatePrivateMovieListVariables>;
export function useCreatePrivateMovieList(dc: DataConnect, options?: useDataConnectMutationOptions<CreatePrivateMovieListData, FirebaseError, CreatePrivateMovieListVariables>): UseDataConnectMutationResult<CreatePrivateMovieListData, CreatePrivateMovieListVariables>;

export function useGetMyPrivateMovieLists(options?: useDataConnectQueryOptions<GetMyPrivateMovieListsData>): UseDataConnectQueryResult<GetMyPrivateMovieListsData, undefined>;
export function useGetMyPrivateMovieLists(dc: DataConnect, options?: useDataConnectQueryOptions<GetMyPrivateMovieListsData>): UseDataConnectQueryResult<GetMyPrivateMovieListsData, undefined>;
