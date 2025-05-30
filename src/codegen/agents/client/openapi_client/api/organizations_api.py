"""Developer API

API for application developers

The version of the OpenAPI document: 1.0.0
Generated by OpenAPI Generator (https://openapi-generator.tech)

Do not edit the class manually.
"""

from typing import Annotated, Any

from pydantic import Field, StrictFloat, StrictInt, StrictStr, validate_call

from codegen.agents.client.openapi_client.api_client import ApiClient, RequestSerialized
from codegen.agents.client.openapi_client.api_response import ApiResponse
from codegen.agents.client.openapi_client.models.page_organization_response import PageOrganizationResponse
from codegen.agents.client.openapi_client.rest import RESTResponseType


class OrganizationsApi:
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None) -> None:
        if api_client is None:
            api_client = ApiClient.get_default()
        self.api_client = api_client

    @validate_call
    def get_organizations_v1_organizations_get(
        self,
        skip: Annotated[int, Field(strict=True, ge=0)] | None = None,
        limit: Annotated[int, Field(le=100, strict=True, ge=1)] | None = None,
        authorization: Any | None = None,
        _request_timeout: None | Annotated[StrictFloat, Field(gt=0)] | tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]] = None,
        _request_auth: dict[StrictStr, Any] | None = None,
        _content_type: StrictStr | None = None,
        _headers: dict[StrictStr, Any] | None = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> PageOrganizationResponse:
        """Get Organizations

        Get organizations for the authenticated user.  Returns a paginated list of all organizations that the authenticated user is a member of. Results include basic organization details such as name, ID, and membership information. Use pagination parameters to control the number of results returned.

        :param skip:
        :type skip: int
        :param limit:
        :type limit: int
        :param authorization:
        :type authorization: object
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """  # noqa: E501
        _param = self._get_organizations_v1_organizations_get_serialize(
            skip=skip, limit=limit, authorization=authorization, _request_auth=_request_auth, _content_type=_content_type, _headers=_headers, _host_index=_host_index
        )

        _response_types_map: dict[str, str | None] = {
            "200": "PageOrganizationResponse",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    @validate_call
    def get_organizations_v1_organizations_get_with_http_info(
        self,
        skip: Annotated[int, Field(strict=True, ge=0)] | None = None,
        limit: Annotated[int, Field(le=100, strict=True, ge=1)] | None = None,
        authorization: Any | None = None,
        _request_timeout: None | Annotated[StrictFloat, Field(gt=0)] | tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]] = None,
        _request_auth: dict[StrictStr, Any] | None = None,
        _content_type: StrictStr | None = None,
        _headers: dict[StrictStr, Any] | None = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[PageOrganizationResponse]:
        """Get Organizations

        Get organizations for the authenticated user.  Returns a paginated list of all organizations that the authenticated user is a member of. Results include basic organization details such as name, ID, and membership information. Use pagination parameters to control the number of results returned.

        :param skip:
        :type skip: int
        :param limit:
        :type limit: int
        :param authorization:
        :type authorization: object
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """  # noqa: E501
        _param = self._get_organizations_v1_organizations_get_serialize(
            skip=skip, limit=limit, authorization=authorization, _request_auth=_request_auth, _content_type=_content_type, _headers=_headers, _host_index=_host_index
        )

        _response_types_map: dict[str, str | None] = {
            "200": "PageOrganizationResponse",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )

    @validate_call
    def get_organizations_v1_organizations_get_without_preload_content(
        self,
        skip: Annotated[int, Field(strict=True, ge=0)] | None = None,
        limit: Annotated[int, Field(le=100, strict=True, ge=1)] | None = None,
        authorization: Any | None = None,
        _request_timeout: None | Annotated[StrictFloat, Field(gt=0)] | tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]] = None,
        _request_auth: dict[StrictStr, Any] | None = None,
        _content_type: StrictStr | None = None,
        _headers: dict[StrictStr, Any] | None = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Get Organizations

        Get organizations for the authenticated user.  Returns a paginated list of all organizations that the authenticated user is a member of. Results include basic organization details such as name, ID, and membership information. Use pagination parameters to control the number of results returned.

        :param skip:
        :type skip: int
        :param limit:
        :type limit: int
        :param authorization:
        :type authorization: object
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """  # noqa: E501
        _param = self._get_organizations_v1_organizations_get_serialize(
            skip=skip, limit=limit, authorization=authorization, _request_auth=_request_auth, _content_type=_content_type, _headers=_headers, _host_index=_host_index
        )

        _response_types_map: dict[str, str | None] = {
            "200": "PageOrganizationResponse",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        return response_data.response

    def _get_organizations_v1_organizations_get_serialize(
        self,
        skip,
        limit,
        authorization,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:
        _host = None

        _collection_formats: dict[str, str] = {}

        _path_params: dict[str, str] = {}
        _query_params: list[tuple[str, str]] = []
        _header_params: dict[str, str | None] = _headers or {}
        _form_params: list[tuple[str, str]] = []
        _files: dict[str, str | bytes | list[str] | list[bytes] | list[tuple[str, bytes]]] = {}
        _body_params: bytes | None = None

        # process the path parameters
        # process the query parameters
        if skip is not None:
            _query_params.append(("skip", skip))

        if limit is not None:
            _query_params.append(("limit", limit))

        # process the header parameters
        if authorization is not None:
            _header_params["authorization"] = authorization
        # process the form parameters
        # process the body parameter

        # set the HTTP header `Accept`
        if "Accept" not in _header_params:
            _header_params["Accept"] = self.api_client.select_header_accept(["application/json"])

        # authentication setting
        _auth_settings: list[str] = []

        return self.api_client.param_serialize(
            method="GET",
            resource_path="/v1/organizations",
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth,
        )

    @validate_call
    def get_organizations_v1_organizations_get_0(
        self,
        skip: Annotated[int, Field(strict=True, ge=0)] | None = None,
        limit: Annotated[int, Field(le=100, strict=True, ge=1)] | None = None,
        authorization: Any | None = None,
        _request_timeout: None | Annotated[StrictFloat, Field(gt=0)] | tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]] = None,
        _request_auth: dict[StrictStr, Any] | None = None,
        _content_type: StrictStr | None = None,
        _headers: dict[StrictStr, Any] | None = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> PageOrganizationResponse:
        """Get Organizations

        Get organizations for the authenticated user.  Returns a paginated list of all organizations that the authenticated user is a member of. Results include basic organization details such as name, ID, and membership information. Use pagination parameters to control the number of results returned.

        :param skip:
        :type skip: int
        :param limit:
        :type limit: int
        :param authorization:
        :type authorization: object
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """  # noqa: E501
        _param = self._get_organizations_v1_organizations_get_0_serialize(
            skip=skip, limit=limit, authorization=authorization, _request_auth=_request_auth, _content_type=_content_type, _headers=_headers, _host_index=_host_index
        )

        _response_types_map: dict[str, str | None] = {
            "200": "PageOrganizationResponse",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    @validate_call
    def get_organizations_v1_organizations_get_0_with_http_info(
        self,
        skip: Annotated[int, Field(strict=True, ge=0)] | None = None,
        limit: Annotated[int, Field(le=100, strict=True, ge=1)] | None = None,
        authorization: Any | None = None,
        _request_timeout: None | Annotated[StrictFloat, Field(gt=0)] | tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]] = None,
        _request_auth: dict[StrictStr, Any] | None = None,
        _content_type: StrictStr | None = None,
        _headers: dict[StrictStr, Any] | None = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[PageOrganizationResponse]:
        """Get Organizations

        Get organizations for the authenticated user.  Returns a paginated list of all organizations that the authenticated user is a member of. Results include basic organization details such as name, ID, and membership information. Use pagination parameters to control the number of results returned.

        :param skip:
        :type skip: int
        :param limit:
        :type limit: int
        :param authorization:
        :type authorization: object
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """  # noqa: E501
        _param = self._get_organizations_v1_organizations_get_0_serialize(
            skip=skip, limit=limit, authorization=authorization, _request_auth=_request_auth, _content_type=_content_type, _headers=_headers, _host_index=_host_index
        )

        _response_types_map: dict[str, str | None] = {
            "200": "PageOrganizationResponse",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )

    @validate_call
    def get_organizations_v1_organizations_get_0_without_preload_content(
        self,
        skip: Annotated[int, Field(strict=True, ge=0)] | None = None,
        limit: Annotated[int, Field(le=100, strict=True, ge=1)] | None = None,
        authorization: Any | None = None,
        _request_timeout: None | Annotated[StrictFloat, Field(gt=0)] | tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]] = None,
        _request_auth: dict[StrictStr, Any] | None = None,
        _content_type: StrictStr | None = None,
        _headers: dict[StrictStr, Any] | None = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Get Organizations

        Get organizations for the authenticated user.  Returns a paginated list of all organizations that the authenticated user is a member of. Results include basic organization details such as name, ID, and membership information. Use pagination parameters to control the number of results returned.

        :param skip:
        :type skip: int
        :param limit:
        :type limit: int
        :param authorization:
        :type authorization: object
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """  # noqa: E501
        _param = self._get_organizations_v1_organizations_get_0_serialize(
            skip=skip, limit=limit, authorization=authorization, _request_auth=_request_auth, _content_type=_content_type, _headers=_headers, _host_index=_host_index
        )

        _response_types_map: dict[str, str | None] = {
            "200": "PageOrganizationResponse",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        return response_data.response

    def _get_organizations_v1_organizations_get_0_serialize(
        self,
        skip,
        limit,
        authorization,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:
        _host = None

        _collection_formats: dict[str, str] = {}

        _path_params: dict[str, str] = {}
        _query_params: list[tuple[str, str]] = []
        _header_params: dict[str, str | None] = _headers or {}
        _form_params: list[tuple[str, str]] = []
        _files: dict[str, str | bytes | list[str] | list[bytes] | list[tuple[str, bytes]]] = {}
        _body_params: bytes | None = None

        # process the path parameters
        # process the query parameters
        if skip is not None:
            _query_params.append(("skip", skip))

        if limit is not None:
            _query_params.append(("limit", limit))

        # process the header parameters
        if authorization is not None:
            _header_params["authorization"] = authorization
        # process the form parameters
        # process the body parameter

        # set the HTTP header `Accept`
        if "Accept" not in _header_params:
            _header_params["Accept"] = self.api_client.select_header_accept(["application/json"])

        # authentication setting
        _auth_settings: list[str] = []

        return self.api_client.param_serialize(
            method="GET",
            resource_path="/v1/organizations",
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth,
        )

    @validate_call
    def get_organizations_v1_organizations_get_1(
        self,
        skip: Annotated[int, Field(strict=True, ge=0)] | None = None,
        limit: Annotated[int, Field(le=100, strict=True, ge=1)] | None = None,
        authorization: Any | None = None,
        _request_timeout: None | Annotated[StrictFloat, Field(gt=0)] | tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]] = None,
        _request_auth: dict[StrictStr, Any] | None = None,
        _content_type: StrictStr | None = None,
        _headers: dict[StrictStr, Any] | None = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> PageOrganizationResponse:
        """Get Organizations

        Get organizations for the authenticated user.  Returns a paginated list of all organizations that the authenticated user is a member of. Results include basic organization details such as name, ID, and membership information. Use pagination parameters to control the number of results returned.

        :param skip:
        :type skip: int
        :param limit:
        :type limit: int
        :param authorization:
        :type authorization: object
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """  # noqa: E501
        _param = self._get_organizations_v1_organizations_get_1_serialize(
            skip=skip, limit=limit, authorization=authorization, _request_auth=_request_auth, _content_type=_content_type, _headers=_headers, _host_index=_host_index
        )

        _response_types_map: dict[str, str | None] = {
            "200": "PageOrganizationResponse",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    @validate_call
    def get_organizations_v1_organizations_get_1_with_http_info(
        self,
        skip: Annotated[int, Field(strict=True, ge=0)] | None = None,
        limit: Annotated[int, Field(le=100, strict=True, ge=1)] | None = None,
        authorization: Any | None = None,
        _request_timeout: None | Annotated[StrictFloat, Field(gt=0)] | tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]] = None,
        _request_auth: dict[StrictStr, Any] | None = None,
        _content_type: StrictStr | None = None,
        _headers: dict[StrictStr, Any] | None = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[PageOrganizationResponse]:
        """Get Organizations

        Get organizations for the authenticated user.  Returns a paginated list of all organizations that the authenticated user is a member of. Results include basic organization details such as name, ID, and membership information. Use pagination parameters to control the number of results returned.

        :param skip:
        :type skip: int
        :param limit:
        :type limit: int
        :param authorization:
        :type authorization: object
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """  # noqa: E501
        _param = self._get_organizations_v1_organizations_get_1_serialize(
            skip=skip, limit=limit, authorization=authorization, _request_auth=_request_auth, _content_type=_content_type, _headers=_headers, _host_index=_host_index
        )

        _response_types_map: dict[str, str | None] = {
            "200": "PageOrganizationResponse",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )

    @validate_call
    def get_organizations_v1_organizations_get_1_without_preload_content(
        self,
        skip: Annotated[int, Field(strict=True, ge=0)] | None = None,
        limit: Annotated[int, Field(le=100, strict=True, ge=1)] | None = None,
        authorization: Any | None = None,
        _request_timeout: None | Annotated[StrictFloat, Field(gt=0)] | tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]] = None,
        _request_auth: dict[StrictStr, Any] | None = None,
        _content_type: StrictStr | None = None,
        _headers: dict[StrictStr, Any] | None = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Get Organizations

        Get organizations for the authenticated user.  Returns a paginated list of all organizations that the authenticated user is a member of. Results include basic organization details such as name, ID, and membership information. Use pagination parameters to control the number of results returned.

        :param skip:
        :type skip: int
        :param limit:
        :type limit: int
        :param authorization:
        :type authorization: object
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """  # noqa: E501
        _param = self._get_organizations_v1_organizations_get_1_serialize(
            skip=skip, limit=limit, authorization=authorization, _request_auth=_request_auth, _content_type=_content_type, _headers=_headers, _host_index=_host_index
        )

        _response_types_map: dict[str, str | None] = {
            "200": "PageOrganizationResponse",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)
        return response_data.response

    def _get_organizations_v1_organizations_get_1_serialize(
        self,
        skip,
        limit,
        authorization,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:
        _host = None

        _collection_formats: dict[str, str] = {}

        _path_params: dict[str, str] = {}
        _query_params: list[tuple[str, str]] = []
        _header_params: dict[str, str | None] = _headers or {}
        _form_params: list[tuple[str, str]] = []
        _files: dict[str, str | bytes | list[str] | list[bytes] | list[tuple[str, bytes]]] = {}
        _body_params: bytes | None = None

        # process the path parameters
        # process the query parameters
        if skip is not None:
            _query_params.append(("skip", skip))

        if limit is not None:
            _query_params.append(("limit", limit))

        # process the header parameters
        if authorization is not None:
            _header_params["authorization"] = authorization
        # process the form parameters
        # process the body parameter

        # set the HTTP header `Accept`
        if "Accept" not in _header_params:
            _header_params["Accept"] = self.api_client.select_header_accept(["application/json"])

        # authentication setting
        _auth_settings: list[str] = []

        return self.api_client.param_serialize(
            method="GET",
            resource_path="/v1/organizations",
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth,
        )
