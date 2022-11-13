<a name="QRadar"></a>

## QRadar
Static class providing utility functions for QRadar

**Kind**: global class  

* [QRadar](#QRadar)
    * [.getApplicationId()](#QRadar.getApplicationId) ⇒ <code>Number</code>
    * [.getApplicationBaseUrl([id])](#QRadar.getApplicationBaseUrl) ⇒ <code>String</code>
    * [.getSelectedRows()](#QRadar.getSelectedRows) ⇒ <code>Array</code>
    * [.getItemId()](#QRadar.getItemId) ⇒ <code>String</code>
    * [.rest(args)](#QRadar.rest)
    * [.fetch(path, options)](#QRadar.fetch) ⇒
    * [.getCurrentUser()](#QRadar.getCurrentUser) ⇒ <code>Object</code>
    * [.openOffense(offenseId, [openWindow])](#QRadar.openOffense)
    * [.openAsset(assetId, [openWindow])](#QRadar.openAsset)
    * [.openAssetForIpAddress(ipAddress, [openWindow])](#QRadar.openAssetForIpAddress)
    * [.openEventSearch(aql, [openWindow])](#QRadar.openEventSearch)
    * [.openFlowSearch(aql, [openWindow])](#QRadar.openFlowSearch)
    * [.getNamedService(services, serviceName, serviceVersion)](#QRadar.getNamedService) ⇒ <code>Object</code>
    * [.getNamedServiceEndpoint(service, endpointName)](#QRadar.getNamedServiceEndpoint) ⇒ <code>Object</code>
    * [.buildNamedServiceEndpointRestArgs(restArgs, endpoint, [parameterValues], [bodyValue])](#QRadar.buildNamedServiceEndpointRestArgs) ⇒ <code>Object</code>
    * [.callNamedServiceEndpoint(serviceName, serviceVersion, endpointName, restArgs, [parameterValues], [bodyValue])](#QRadar.callNamedServiceEndpoint)

<a name="QRadar.getApplicationId"></a>

### QRadar.getApplicationId() ⇒ <code>Number</code>
Returns the id of the current application.
<p>
This function can only be used where JavaScript is included using
the page_scripts section of an application manifest.json file.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Returns**: <code>Number</code> - The id of the current application.  
**Throws**:

- Error if application could not be identified.

<a name="QRadar.getApplicationBaseUrl"></a>

### QRadar.getApplicationBaseUrl([id]) ⇒ <code>String</code>
Returns the base URL of an application.
<p>
The format of the returned URL is: https://&lt;ip address&gt;/console/plugins/&lt;app id&gt;/app_proxy
<p>
This function can only be used where JavaScript is included using
the page_scripts section of an application manifest.json file.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Returns**: <code>String</code> - The base URL of an application.  
**Throws**:

- Error if id was not supplied and the current application could not be identified.


| Param | Type | Description |
| --- | --- | --- |
| [id] | <code>Number</code> | The id of an application to get the base URL for.                        If not supplied, the id of the current application is used. |

<a name="QRadar.getSelectedRows"></a>

### QRadar.getSelectedRows() ⇒ <code>Array</code>
Returns the ids of selected rows on a list page such as the offense or asset list.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Returns**: <code>Array</code> - The ids of the selected rows.
                 If no rows are selected, the array will be empty.  
**Throws**:

- Error if the current page does not contain a table of selectable rows.

<a name="QRadar.getItemId"></a>

### QRadar.getItemId() ⇒ <code>String</code>
Returns the id of the item being viewed (e.g. asset, offense).

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Returns**: <code>String</code> - Item id.  
**Throws**:

- Error if the current page does not support item identification.

<a name="QRadar.rest"></a>

### QRadar.rest(args)
Calls a REST method using an XMLHttpRequest.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Throws**:

- Error if any required arguments are missing.


| Param | Type | Default | Description |
| --- | --- | --- | --- |
| args | <code>Object</code> |  |  |
| args.httpMethod | <code>String</code> |  | The HTTP method to use (GET/PUT/POST/DELETE). |
| args.path | <code>String</code> |  | The path to the REST endpoint. <ul> <li> To call a QRadar REST API, path must start with "/api". <li> To call a REST endpoint in your application, path must start with "/application". <li> Any other path must be a fully-qualified URL, otherwise the function behaviour is undefined. </ul> |
| [args.body] | <code>String</code> |  | The data to POST or PUT. |
| [args.onComplete] | <code>function</code> |  | Callback function to be invoked when the REST request finishes.                                       The function can access the XMLHttpRequest using "this". |
| [args.onError] | <code>function</code> |  | Callback function to be invoked if the REST request fails to complete. |
| [args.headers] | <code>Array</code> |  | Headers to be supplied with the REST request.                                 Each array entry should be a JSON object with "name" and "value" properties. |
| [args.contentType] | <code>String</code> | <code>&quot;application/json&quot;</code> | MIME type of a POST or PUT request.                                                         Default value is used only if Content-Type is not                                                         supplied in args.headers. |
| [args.timeout] | <code>Number</code> |  | HTTP timeout, in milliseconds, to be supplied with an asynchronous REST request.                                  If args.async is false, the timeout is ignored. |
| [args.async] | <code>boolean</code> | <code>true</code> | Set to false to make a synchronous request.                                      WARNING: this is not recommended. |

<a name="QRadar.fetch"></a>

### QRadar.fetch(path, options) ⇒
Uses the fetch API (or polyfilled alternative) to make a HTTP request, returning a promise.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Returns**: Fetch promise that when resolved executed the request  

| Param | Type | Description |
| --- | --- | --- |
| path | <code>String</code> | The path to the endpoint. <ul> <li> To call a QRadar REST API, path must start with "/api". <li> To call a REST endpoint in your application, path must start with "/application". <li> Any other path must be a fully-qualified URL, otherwise the function behaviour is undefined. </ul> |
| options | <code>Object</code> | Fetch options, defining method, headers etc. Includes a timeout. See https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch#Supplying_request_options |
| [args.timeout] | <code>Number</code> | How long to wait before timing out the request, default 10000ms (10 seconds) |
| [args.credentials] | <code>String</code> | CORS credentials type to use, default "same-origin" |
| [args.headers] | <code>Array</code> | Headers included in the request, default ["Content-Type": "application/json"] |

<a name="QRadar.getCurrentUser"></a>

### QRadar.getCurrentUser() ⇒ <code>Object</code>
Returns information on the currently logged in QRadar user, including their name and role.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Returns**: <code>Object</code> - The currently logged in QRadar user.
                  WARNING this function uses a synchronous JavaScript call.  
<a name="QRadar.openOffense"></a>

### QRadar.openOffense(offenseId, [openWindow])
Opens the details page of an offense, either in a new window or in the Offenses tab.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Throws**:

- Error if offenseId is not supplied or if the offense could not be displayed.


| Param | Type | Default | Description |
| --- | --- | --- | --- |
| offenseId | <code>String</code> \| <code>Number</code> |  | The id of the offense to be viewed. |
| [openWindow] | <code>boolean</code> | <code>true</code> | If true, open the result in a new window.                                      Otherwise, open in the Offenses tab. |

<a name="QRadar.openAsset"></a>

### QRadar.openAsset(assetId, [openWindow])
Opens the details page of an asset, either in a new window or in the Assets tab.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Throws**:

- Error if assetId is not supplied or if the asset could not be displayed.


| Param | Type | Default | Description |
| --- | --- | --- | --- |
| assetId | <code>String</code> \| <code>Number</code> |  | The id of the asset to be viewed. |
| [openWindow] | <code>boolean</code> | <code>true</code> | If true, open the result in a new window.                                      Otherwise, open in the Assets tab. |

<a name="QRadar.openAssetForIpAddress"></a>

### QRadar.openAssetForIpAddress(ipAddress, [openWindow])
Opens the details page of an asset for an IP address, either in a new window or in the Assets tab.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Throws**:

- Error if ipAddress is not supplied or if the asset could not be displayed.


| Param | Type | Default | Description |
| --- | --- | --- | --- |
| ipAddress | <code>String</code> |  | The IP address of the asset to be viewed. |
| [openWindow] | <code>boolean</code> | <code>true</code> | If true, open the result in a new window.                                      Otherwise, open in the Assets tab. |

<a name="QRadar.openEventSearch"></a>

### QRadar.openEventSearch(aql, [openWindow])
Runs an event search with the specified AQL string, either in a new window or the Event Viewer tab.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Throws**:

- Error if aql is not supplied or if the search results could not be displayed.


| Param | Type | Default | Description |
| --- | --- | --- | --- |
| aql | <code>String</code> |  | The AQL search string to execute. |
| [openWindow] | <code>boolean</code> | <code>true</code> | If true, open the search in a new window.                                      Otherwise, open in the Event Viewer tab. |

<a name="QRadar.openFlowSearch"></a>

### QRadar.openFlowSearch(aql, [openWindow])
Runs a flow search with the specified AQL string, either in a new window or the Flow Viewer tab.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Throws**:

- Error if aql is not supplied or if the search results could not be displayed.


| Param | Type | Default | Description |
| --- | --- | --- | --- |
| aql | <code>String</code> |  | The AQL search string to execute. |
| [openWindow] | <code>boolean</code> | <code>true</code> | If true, open the search in a new window.                                      Otherwise, open in the Flow Viewer tab. |

<a name="QRadar.getNamedService"></a>

### QRadar.getNamedService(services, serviceName, serviceVersion) ⇒ <code>Object</code>
Selects and returns a service from a list retrieved by a /gui_app_framework/named_services
REST API call.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Returns**: <code>Object</code> - The service with the given name and version from the services list.  
**Throws**:

- Error if the services list did not contain an entry with the given name and version.


| Param | Type | Description |
| --- | --- | --- |
| services | <code>Array</code> | The array returned by /gui_app_framework/named_services. |
| serviceName | <code>String</code> | The name of the service to look for in services. |
| serviceVersion | <code>String</code> | The version of the service to look for in services. |

<a name="QRadar.getNamedServiceEndpoint"></a>

### QRadar.getNamedServiceEndpoint(service, endpointName) ⇒ <code>Object</code>
Selects and returns a service endpoint.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Returns**: <code>Object</code> - The service endpoint with the given name.  
**Throws**:

- Error if the service object did not contain an endpoint with the given name.


| Param | Type | Description |
| --- | --- | --- |
| service | <code>Object</code> | A service object as returned by [getNamedService](#QRadar.getNamedService). |
| endpointName | <code>String</code> | The name of the endpoint to look for in the service object. |

<a name="QRadar.buildNamedServiceEndpointRestArgs"></a>

### QRadar.buildNamedServiceEndpointRestArgs(restArgs, endpoint, [parameterValues], [bodyValue]) ⇒ <code>Object</code>
Populates an arguments object to be used in a [rest](#QRadar.rest) call to a named service endpoint.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Returns**: <code>Object</code> - restArgs populated with properties from endpoint, parameterValues and bodyValue.  
**Throws**:

- Error if a parameterValue property was not supplied for each endpoint PATH parameter.

**See**: [rest](#QRadar.rest)  

| Param | Type | Description |
| --- | --- | --- |
| restArgs | <code>Object</code> | A possibly empty object which will be populated with arguments for a                            call to [rest](#QRadar.rest). The properties of restArgs which can be                            populated by this function are: httpMethod, path, body and contentType.                            All other properties must be populated by the caller. |
| endpoint | <code>Object</code> | A service endpoint object as returned                            by [getNamedServiceEndpoint](#QRadar.getNamedServiceEndpoint). |
| [parameterValues] | <code>Object</code> | Contains properties whose values will be used to populate the                                     endpoint's PATH/QUERY/BODY parameters. |
| [bodyValue] | <code>Object</code> | A complete body value to be supplied with a POST or PUT. |

<a name="QRadar.callNamedServiceEndpoint"></a>

### QRadar.callNamedServiceEndpoint(serviceName, serviceVersion, endpointName, restArgs, [parameterValues], [bodyValue])
Makes a REST API call to a named service endpoint.
<p>
This is a wrapper function which calls the /gui_app_framework/named_services REST API,
picks out the specified service endpoint, and invokes it using the supplied parameters/values.

**Kind**: static method of [<code>QRadar</code>](#QRadar)  
**Throws**:

- Error if any wrapped function call fails.


| Param | Type | Description |
| --- | --- | --- |
| serviceName | <code>String</code> | See [getNamedService](#QRadar.getNamedService) serviceName. |
| serviceVersion | <code>String</code> | See [getNamedService](#QRadar.getNamedService) serviceVersion. |
| endpointName | <code>String</code> | See [getNamedServiceEndpoint](#QRadar.getNamedServiceEndpoint) endpointName. |
| restArgs | <code>Object</code> | See [buildNamedServiceEndpointRestArgs](#QRadar.buildNamedServiceEndpointRestArgs) restArgs. |
| [parameterValues] | <code>Object</code> | See [buildNamedServiceEndpointRestArgs](#QRadar.buildNamedServiceEndpointRestArgs) parameterValues. |
| [bodyValue] | <code>Object</code> | See [buildNamedServiceEndpointRestArgs](#QRadar.buildNamedServiceEndpointRestArgs) bodyValue. |

