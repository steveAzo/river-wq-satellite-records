# Freeze record for the second confirmation

Written 2026-10-26 07:26 UTC. Commit 86f662b9d84d7ce5ea67c90b8fb0f37c892741a4, tag `confirm2-freeze`.
The sealed cohort had not been read when this record was written.

| File | MD5 |
|---|---|
| `src/p3\__init__.py` | d41d8cd98f00b204e9800998ecf8427e |
| `src/p3\analytic.py` | d05391875e998cc079e6c5080aa3e16a |
| `src/p3\bench.py` | cf30c6e92d5171d37a7165d874c73821 |
| `src/p3\bootstrap.py` | fc703abea81661b01ea0d87de4ea02c6 |
| `src/p3\channel.py` | e44b889401a07a9e6477a955cac42da5 |
| `src/p3\cohort.py` | cbff647d063d92227bf9d533943ae1b9 |
| `src/p3\cohort2.py` | 155327ef7f2b4271f71f77fc683dd1c1 |
| `src/p3\cohort_exact.py` | d8b3655a1603dcf36c9d5c28a65fb6b7 |
| `src/p3\confirm2.py` | f96c54e3de0e74bdcf0f2e61c50aea16 |
| `src/p3\confirm_pooling.py` | 451595f22700515e0a47d1b3e393d0dd |
| `src/p3\data.py` | 6da3929182f7987d9ba3802e46d7be01 |
| `src/p3\delivery.py` | daa81e1bc4beec491b7625e793a8c6ce |
| `src/p3\designs.py` | eee119710549bfc17635ecf5cc3202bf |
| `src/p3\e2_anchor.py` | 08f1a92e9be7794d627415a5d73e0abf |
| `src/p3\env.py` | 03ad568ece02d928d7d53c6cc6b964a8 |
| `src/p3\env_eval.py` | 5287cf854ae00e7d241e5aa4fe981622 |
| `src/p3\fountain.py` | c2478649ed4774b27d4565f241ecfa40 |
| `src/p3\frame.py` | 5dba721a9ff647b7093e470bf2150fa3 |
| `src/p3\frame_example.py` | c2ea7d864ba7bab66c721b926fba6468 |
| `src/p3\loader.py` | 1b73bc2c2d8584f135ff7bcb99019592 |
| `src/p3\lowcost.py` | 6aff62a0c0748cdc8a84e6e53c09007c |
| `src/p3\multiday.py` | 51c6e7bf64043922f0516a4ecfe92033 |
| `src/p3\multiday_eval.py` | 43d73a8cd5ef0c8e63131af223028fd1 |
| `src/p3\need.py` | 9c6a13a21677c62433b7aee81361257a |
| `src/p3\need2.py` | 615cc5be8e0caa30f9c8867ac9214cac |
| `src/p3\need_modes.py` | 0cc8681504fe8fa5eaec774ccd052966 |
| `src/p3\pla.py` | 85f5c446532a6e55b5f3678664dcd0cf |
| `src/p3\pooling.py` | 29ffa9af5e0da4eb38e642dfd476802e |
| `src/p3\record.py` | ad2ddabde44e8b9cc1c468bc23afe2f1 |
| `src/p3\robust_bytes.py` | daae4baf77b65e380522f636f94a56b8 |
| `src/p3\robust_eval.py` | 9b191c61cd620b4f6a22f738fc2f6348 |
| `src/p3\robustness.py` | 503bac60a39b807ccf958dd4507ef8aa |
| `src/p3\rs.py` | 928300f42aaad67c70813c68eb880577 |
| `src/p3\run_confirm.py` | 6a49a45ae3036a63496fb17b536a8641 |
| `src/p3\run_dev.py` | 271cbeb27e54318dabbe158fb7290f99 |
| `src/p3\run_e2e.py` | 78fbe6277f3e7570fc93fbe66b32b69f |
| `src/p3\run_env.py` | f7208338f7bc7f8a15bd3094407100c4 |
| `src/p3\run_multiday.py` | f9151655d7bc7da0d5aa9bc569aa6a6a |
| `src/p3\run_robust.py` | a0c99145fb0e4fc8400842f31a02076e |
| `src/p3\sens_rq3.py` | 7ab092174c8fea0182459ffb4b852bb2 |
| `src/p3\sensitivity.py` | f1981c12134590324171d50b72b44ff1 |
| `src/p3\server.py` | bdbe996097b36b75b934f0e3864476e9 |
| `src/p3\stats.py` | 15ac181f83b04a6256607449b5069957 |
| `src/p3\stream.py` | 3e05b8a7add0f4740c5fce4cd4e3ace2 |
| `src/data\__init__.py` | d41d8cd98f00b204e9800998ecf8427e |
| `src/data\clean_usgs.py` | 235c2d56e12d52eed941d2f74acba891 |
| `src/data\fetch_usgs.py` | ea6d3d7b8faae4f9b87d44396486ac46 |
| `src/data\freeze2.py` | 9495d38034d664fdf9f0aebbf3134b08 |
| `src/data\seal.py` | 00e37a6f604160ca38e95254ff73f2a6 |
| `src/data\select_new_cohort.py` | e35edd9cbcaccdd3ec373773a3159f43 |
| `docs/CONFIRM2_PLAN.md` | b838dac354f99c07486f78cafad2c5d7 |
| `results/dev/robust_choice.json` | 573df9a83b929bbca832982f73922459 |
| `results/dev/stats_rq4.csv` | 45c0b4b998cfa497185b3b1e7c174c1a |
| `data/raw/usgs_new2024.md5` | 003bf2fb04d424c9b6786b7f968e3c4a |
| `data/clean/usgs_new2024.md5` | 38ff306d4528510e1011996841a41b0d |
