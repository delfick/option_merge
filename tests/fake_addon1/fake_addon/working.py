def __option_merge__(configuration, result_maker, **kwargs):
    return result_maker(post_register=post_register)

def post_register(result, configuration, **kwargs):
	configuration.update({"injected": True})
