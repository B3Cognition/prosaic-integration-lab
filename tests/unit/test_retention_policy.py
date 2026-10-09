from prosaic_integration_lab.retention import classification

def test_uncertain_or_unknown_evidence_is_never_selected_for_destructive_retirement():
    assert classification({'phase':'starting'},{'status':'completed'},{'unresolved_calls':0})=='retain_uncertain'
    assert classification({'phase':'started'},{'status':'completed'},{'unresolved_calls':1})=='retain_unresolved'
    assert classification({'phase':'started'},{'status':'waiting'},{'unresolved_calls':0})=='retain_unresolved'

def test_known_terminal_run_is_only_a_copy_candidate_not_a_deletion_authorization():
    assert classification({'phase':'started'},{'status':'completed'},{'unresolved_calls':0})=='terminal_copy'
