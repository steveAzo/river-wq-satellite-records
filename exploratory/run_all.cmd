@echo off
rem POST HOC exploratory runs for the outside review (points 2, 5, 6, 7, 8). Run from Paper3\. Resumable (per-site outputs).
cd /d "%~dp0.."
echo START %date% %time%>> exploratory\run_all.log
python -I -W ignore exploratory\explore4.py data\clean\usgs rehearsal4_2023 >> exploratory\run_all.log 2>&1
echo DONE explore 2023 %date% %time%>> exploratory\run_all.log
python -I -W ignore exploratory\explore4.py data\clean\usgs_new3_2024 rehearsal4v2 >> exploratory\run_all.log 2>&1
echo DONE explore 2024 %date% %time%>> exploratory\run_all.log
python -I -W ignore exploratory\explore4.py data\clean\usgs_new4_2022 confirm4 >> exploratory\run_all.log 2>&1
echo DONE explore 2022 %date% %time%>> exploratory\run_all.log
python -I -W ignore exploratory\run_baselines.py data\clean\usgs rehearsal4_2023 >> exploratory\run_all.log 2>&1
echo DONE baselines 2023 %date% %time%>> exploratory\run_all.log
python -I -W ignore exploratory\run_baselines.py data\clean\usgs_new3_2024 rehearsal4v2 >> exploratory\run_all.log 2>&1
echo DONE baselines 2024 %date% %time%>> exploratory\run_all.log
python -I -W ignore exploratory\run_baselines.py data\clean\usgs_new4_2022 confirm4 >> exploratory\run_all.log 2>&1
echo DONE baselines 2022 %date% %time%>> exploratory\run_all.log
echo ALL DONE>> exploratory\run_all.log
