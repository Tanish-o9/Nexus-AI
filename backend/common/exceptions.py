from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def nexus_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        import traceback
        traceback.print_exc()
        # Unhandled exception — return 500 with safe message
        return Response(
            {'error': 'internal_server_error', 'detail': 'An unexpected error occurred.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Normalize DRF's varied error shapes into one consistent envelope
    detail = response.data

    if isinstance(detail, dict):
        # Flatten single-key {'detail': '...'} responses
        if list(detail.keys()) == ['detail']:
            detail = str(detail['detail'])
        # Otherwise keep the field-level error dict as-is (validation errors)
    elif isinstance(detail, list):
        detail = detail[0] if len(detail) == 1 else detail

    response.data = {
        'error': _status_to_code(response.status_code),
        'detail': detail,
    }
    return response


def _status_to_code(status_code: int) -> str:
    mapping = {
        400: 'bad_request',
        401: 'unauthorized',
        403: 'forbidden',
        404: 'not_found',
        405: 'method_not_allowed',
        409: 'conflict',
        429: 'too_many_requests',
        500: 'internal_server_error',
    }
    return mapping.get(status_code, 'error')
