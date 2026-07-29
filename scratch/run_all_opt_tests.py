import sys
import os
sys.path.insert(0, r"c:\GitHub\Siti\CutMob")

import test_optimizer

test_optimizer.test_full_width_bar_prioritization()
test_optimizer.test_bar_cutting_logic_vs_for_reduced_width()
test_optimizer.test_grain_rotation_and_selection()
test_optimizer.test_new_warehouse_selection_logic()
test_optimizer.test_remnants_orientation_and_matching()
test_optimizer.test_sfrido_only_on_panels()
test_optimizer.test_sfrido()
test_optimizer.test_rifilo()
test_optimizer.test_nesting_pantografo()
test_optimizer.test_optimization()
test_optimizer.test_guillotine_and_semilavorati()
test_optimizer.test_requirement_simulation()
test_optimizer.test_new_csv_format_and_duplicates()
test_optimizer.test_new_order_csv_format_and_alignment()
test_optimizer.test_semilavorati_csv_import()
test_optimizer.test_remnants_prioritization_and_exclusion()
test_optimizer.test_panel_production()
test_optimizer.test_commesse_persistence()
test_optimizer.test_bar_height_alignment()
test_optimizer.test_tall_pieces_routing_to_panels()
test_optimizer.test_standard_bar_height_constraint()
test_optimizer.test_filtering_and_f3_optimization()
test_optimizer.test_commessa_delete_and_clear_filters()

print("\nALL OPTIMIZER TESTS PASSED PERFECTLY!")
