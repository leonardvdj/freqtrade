docker manifest create leonardvdj/freqtrade:develop --amend leonardvdj/freqtrade:develop_amd64 --amend leonardvdj/freqtrade:develop_arm64
docker manifest push leonardvdj/freqtrade:develop
docker manifest rm leonardvdj/freqtrade:develop