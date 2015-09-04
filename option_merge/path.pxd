cdef class Path:
    cdef public path
    cdef public converters
    cdef public configuration
    cdef public ignore_converters

    cdef str _joined
    cdef path_type
    cdef path_is_string
    cdef _joined_function
