from hfc_thrift.rdfproxy import RdfProxy

def get_user_session_pairs(first_name: str, last_name: str):      
    user_session_pairs = RdfProxy.selectQuery('select distinct ?user ?sess where ?user <rdf:type> <cim:User> ?_ '
                                            '& ?user <cim:userSessions> ?sess ?_ '
                                            '& ?user <soho:hasName> "{first_name}" ?_ '
                                            '& ?user  <soho:hasSurname> "{last_name}" ?_'.format(first_name=first_name,last_name=last_name))
    return user_session_pairs

def init_proxy():
    port=7070
    RdfProxy.init_rdfproxy(port=port)

def update_strategy(num_sessions, blackboard):
    strategy = []

    init_proxy()
    
    first_name = blackboard.get("first_name")
    last_name = blackboard.get("last_name")

    user_session_pairs = get_user_session_pairs(first_name,last_name)

    # TODO: reasoning based on session data 

    blackboard.set("strategy", strategy)