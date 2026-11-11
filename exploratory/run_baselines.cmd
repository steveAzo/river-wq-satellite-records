@echo off
rem POST HOC baselines for the outside review (point 5): sealed cohort first, then the 2023 development year. Resumable.
cd /d "%~dp0.."
echo START baselines %date% %time%>> exploratory\run_all.log
python -I -W ignore exploratory\run_baselines.py data\clean\usgs_new4_2022 confirm4 >> exploratory\run_all.log 2>&1
echo DONE baselines 2022 %date% %time%>> exploratory\run_all.log
python -I -W ignore exploratory\run_baselines.py data\clean\usgs rehearsal4_2023 >> exploratory\run_all.log 2>&1
echo DONE baselines 2023 %date% %time%>> exploratory\run_all.log
echo ALL BASELINES DONE>> exploratory\run_all.log
